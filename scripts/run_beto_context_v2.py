"""One frozen representation, three-run pilot, automatic preregistered expansion."""
import json
import traceback
from datetime import datetime,timezone
import run_beto_first_training_v2 as b
from prepare_beto_context_v2 import OUT,ART,encode

ENCODED={}

def context_loader(rows,tok,length,shuffle=False,seed=42):
    import torch
    assert length==384
    keys=['input_ids','token_type_ids','attention_mask']
    data=torch.utils.data.TensorDataset(*[torch.tensor([ENCODED[r['segment_id']]['transformed'][k] for r in rows]) for k in keys],
        torch.tensor([b.LABELS.index(r['label']) for r in rows]))
    return torch.utils.data.DataLoader(data,batch_size=2,shuffle=shuffle,generator=torch.Generator().manual_seed(seed),num_workers=0),keys

def save_same(path,value):
    if path.exists():assert b.read(path)==value,f'Existing artifact differs: {path}'
    else:b.save(path,value)

def verify():
    from transformers import AutoTokenizer
    p,byid=b.inputs();cp=b.read(ART/'protocol.json')
    for path,sha in cp['frozen_hashes'].items():assert b.filehash(b.ROOT/path)==sha,path
    for source in cp['sources'].values():assert b.filehash(b.ROOT/source['path'])==source['sha256']
    ENCODED.update(b.read(OUT/'inputs.json'))
    manifest=b.read(ART/'manifest.json')['items'];assert set(ENCODED)==set(byid)
    tok=AutoTokenizer.from_pretrained(b.BASE,revision=b.REV,local_files_only=True)
    # Compare against the original batched tokenizer, including padding and type IDs.
    original=tok([r['text'] for r in byid.values()],padding='max_length',truncation=True,max_length=384)
    for i,(sid,r) in enumerate(byid.items()):
        item=ENCODED[sid];assert item['target_text']==r['text']
        assert item['original']=={k:v[i] for k,v in original.items()}
        a,z,t,c=encode(tok,r['text'],item['context']);assert a==item['original'] and z==item['transformed']
        m=next(x for x in manifest if x['segment_id']==sid)
        assert b.fingerprint(a)==m['original_input_sha256'] and b.fingerprint(z)==m['transformed_input_sha256']
        assert sum(z['attention_mask'])<=384 and len(c)<=95
    # Boundary checks exercise no-context, saturated target and only one available context token.
    for n in [1,379,380,381,382,400]:
        for context in ['', 'historia peruana anterior']:
            a,z,t,c=encode(tok,' '.join(['casa']*n),context)
            assert z['input_ids'][1:1+len(t)]==t
            if not c:assert a==z
            else:assert z['token_type_ids'][len(t)+2:len(t)+3]==[1]
    audit=b.read(ART/'alignment-audit.json');assert audit['passed'] and audit['sample_sha256']==b.filehash(OUT/'alignment-sample.json')
    checks={'rows':591,'target_tokens_preserved':True,'batched_B_inputs_identical':True,'boundary_checks':12,
            'inputs_sha256':b.filehash(OUT/'inputs.json'),'runner_sha256':b.filehash(b.ROOT/'scripts/run_beto_context_v2.py')}
    save_same(ART/'checks.json',checks)
    return p,byid,cp,manifest

def control(seed,fold,p,val):
    if seed==42:dest=b.OUT/'runs'/(fold['id']+'-B');config=p
    else:
        dest=b.ROOT/'outputs/beto-v2/stability'/f'seed-{seed}'/(fold['id']+'-B');config=b.read(dest/'config.json')
    return b.verify_result(dest,config,val)

def gate(p,byid,cp,manifest):
    differences=[]
    for f in p['folds']:
        base=control(42,f,p,[byid[i] for i in f['validation']])
        result=b.read(OUT/'seed-42'/(f['id']+'-B_context')/'result.json')
        differences.append({k:result['metrics'][k]['f1_macro']-base['metrics'][k]['f1_macro'] for k in ['combined','historical']})
    rule=cp['expansion_gate'];families=sorted({m['family_id'] for m in manifest if m['changed'] and m['role']=='historical_train'})
    checks={'mean_combined_delta':sum(d['combined'] for d in differences)/3,
            'improved_folds':sum(d['combined']>0 for d in differences),'mean_historical_delta':sum(d['historical'] for d in differences)/3,
            'historical_families':families}
    passed=(checks['mean_combined_delta']>=rule['minimum_mean_combined_delta'] and checks['improved_folds']>=rule['minimum_improved_folds']
        and checks['mean_historical_delta']>=rule['minimum_mean_historical_delta'] and len(families)>=rule['minimum_historical_families_with_context'])
    result={'rule':rule,'observed':checks,'passed':passed,'paired_fold_differences':differences}
    save_same(ART/'pilot-gate.json',result);return passed

def main():
    p,byid,cp,manifest=verify()
    if not any(m['changed'] for m in manifest):
        save_same(ART/'blocked.json',{'reason':'No valid changed inputs; no training'});return
    b.loader=context_loader
    for seed in [42,43,44]:
        if seed!=42 and not gate(p,byid,cp,manifest):break
        for fold in p['folds']:
            train=[byid[i] for i in fold['train_B']];val=[byid[i] for i in fold['validation']]
            base=control(seed,fold,p,val)
            dest=OUT/f'seed-{seed}'/(fold['id']+'-B_context')
            config={**p,'execution':{'seed':seed,'fold':fold['id'],'condition':'B_context','train_rows_hash':b.fingerprint(train),
                'validation_rows_hash':b.fingerprint(val),'context_protocol_hash':b.fingerprint(cp),'runner_sha256':b.filehash(b.ROOT/'scripts/run_beto_context_v2.py')}}
            save_same(dest/'config.json',config)
            if (dest/'result.json').exists():result=b.verify_result(dest,config,val)
            else:
                event={'at_utc':datetime.now(timezone.utc).isoformat(),'seed':seed,'fold':fold['id'],'resume_files':[x.name for x in dest.glob('resume-epoch-*.pt')]}
                try:
                    result=b.train_run(train,val,dest,config)
                    event['status']='complete'
                except Exception as exc:
                    event.update(status='failed',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
                    raise
                finally:
                    with (OUT/'execution-events.jsonl').open('a',encoding='utf-8') as file:file.write(json.dumps(event)+'\n')
            assert result['class_weights']==base['class_weights'] and result['steps_per_epoch']==base['steps_per_epoch']
    from report_beto_context_v2 import report
    report()

if __name__=='__main__':main()
