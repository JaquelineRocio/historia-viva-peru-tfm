"""Adjudication, canonical view and documentary development folds, before predictions."""
import csv
import importlib.metadata
import unicodedata
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from run_beto_first_training_v2 import *

REVIEW = {
'S01-seg0005-s00000':'R5: educación republicana desde 1821 es la consecuencia explicada; el orden virreinal es antecedente.',
'S01-seg0005-s02191':'R5: prensa y saberes destinados al funcionamiento del modelo republicano y formación ciudadana.',
'S01-seg0007-s01472':'PENDIENTE: innovación constitucional y hegemonía colonial tienen desarrollo sustantivo; el contexto no fija dominancia.',
'S01-seg0007-s04313':'R2: crisis de 1808–1812 explica divulgación liberal, nación y nuevo lenguaje gaditano.',
'S01-seg0007-s06192':'R2: el procedimiento de jura materializa el traslado de soberanía del rey a la nación en 1812.',
'S01-seg0007-s05495':'R5: el hilo es la reutilización efectiva del ritual de autoridad en la gira de Bolívar de 1825; el antecedente colonial explica esa continuidad. Resuelve la alerta B conservando R1 como alternativa.',
'S01-seg0008-s00000':'R5: implantación ritual y prohibición efectiva de festivales coloniales, no propuesta de régimen.',
'S01-seg0010-s02676':'R4: resistencia organizada al proyecto constitucional vitalicio; disputa de poder, no administración ordinaria.',
'S03-seg0005-s00000':'R1: capacidad y organización naval colonial durante siete décadas; contexto enlaza con el departamento del Callao y la independencia.',
'S03-seg0017-s00000':'R3: refuerzo y habilitación de buques como respuesta logística al peligro militar.',
'S03-seg0019-s00000':'R3: protección de tropas y nuevo reto naval tras la derrota realista en Chile.',
'S03-seg0022-s00000':'R3: refuerzos navales y control del mar para impedir invasión; nombres de mandos no desplazan la logística.',
'S03-seg0062-s00000':'R3: el control militar del mar explica la capacidad expedicionaria y su pérdida.',
'S06-seg0008-s00000':'PENDIENTE: desembarco y crisis liberal se yuxtaponen; no forzar R2 para cubrir carencia.',
'S06-seg0010-s00000':'R6: reacción, incentivos e indiferencia de grupos populares ante la proclamación constitucional; no doctrina política como eje.',
'S06-seg0022-s00000':'R3: el convenio de señales explica el engaño táctico durante el combate.',
'S06-seg0035-s00000':'R4: envío de cónsules y reconocimiento tácito de independencia constituyen el argumento diplomático.',
'S06-seg0040-s00000':'R6: crítica de testimonios concluye sobre actitudes populares ante separatismo; contenido histórico sustantivo.',
'S10-seg0010-s00717':'R6: representación racializada y condiciones indígenas en discurso de 1827; no norma aplicada como tema principal.',
'S10-seg0012-s00000':'R5: puesta en práctica de enseñanza religiosa y Escuela Normal en 1822.',
'S10-seg0015-s00645':'PENDIENTE: la reedición desde 1860 no fecha por sí sola los planteamientos. Sin etiqueta negativa definitiva.',
'S15-seg0010-s00000':'R1: valor económico de mano de obra esclavizada colonial; contexto desarrolla su transformación a fines del XVIII y tras independencia.',
'S15-seg0017-s00000':'R7: inventario de secciones y fuentes de un periódico; mención del Congreso sin explicación de su funcionamiento o efectos.',
}

def norm(t):return ' '.join(unicodedata.normalize('NFKC',t).casefold().split())

def annotations():
    packet=read(OUT/'annotation-input.json');cfg=packet['config'];targets={r['segment_id']:r for r in packet['items']}
    assert set(targets)==set(REVIEW)
    decisions={};cache_index=[]
    for name in ['A','B']:
        records=read(OUT/f'pass-{name.lower()}.json')['items'];assert len(records)==len(targets)
        decisions[name]={r['segment_id']:r for r in records};assert set(decisions[name])==set(targets)
        for r in records:
            t=targets[r['segment_id']]
            assert r['label'] in LABELS and r['alternative_label'] in LABELS+[None]
            assert r['family_id']==t['family_id'] and t['text'][r['evidence_start']:r['evidence_end']]==r['evidence']
            payload={'text':t['text'],'context':t['context'],'guide_sha256':cfg['guide_sha256'],'configuration':{**cfg,'pass':name}}
            key=fingerprint(payload);old=ROOT/'outputs/beto-v2/pilot/cache'/name/(key+'.json')
            assert not old.exists(),'Matching prior cache should have been reused'
            path=OUT/'cache'/name/(key+'.json')
            save(path,{**r,**payload,'cache_key':key,'annotation_origin':'AI-assisted, not expert gold'})
            cache_index.append({'segment_id':r['segment_id'],'pass':name,'key':key,'path':path.relative_to(ROOT).as_posix(),'sha256':filehash(path)})
    candidates={r['segment_id']:r for r in [json.loads(s) for s in (ROOT/'outputs/beto-v2/pilot/annotation-candidates-final.jsonl').read_text(encoding='utf-8').splitlines()]}
    provenance={r['segment_id']:r for r in read(ROOT/'outputs/beto-v2/pilot/provenance-final-recovered.json')}
    adjud=[];new=[]
    for sid,t in targets.items():
        a,b=decisions['A'][sid],decisions['B'][sid]
        assert a['label']==b['label'],'Unreviewed class disagreement'
        pending=REVIEW[sid].startswith('PENDIENTE')
        label=None if pending else a['label']
        adjud.append({'segment_id':sid,'final_label':label,'rationale':REVIEW[sid],'pass_a':a,'pass_b':b,'annotation_origin':'AI-assisted, not expert gold','status':'pending_ambiguity' if pending else 'accepted_AI_assisted','guide_sha256':cfg['guide_sha256']})
        new.append({**candidates[sid],'label':label,'annotation_status':adjud[-1]['status'],'pages_exact':provenance[sid]['pages_exact'],'annotation_origin':'AI-assisted, not expert gold'})
    save(OUT/'adjudication.json',{'items':adjud});save(OUT/'cache-index.json',cache_index)
    save(OUT/'additional-annotated.json',{'items':new})
    save(ART/'annotation-summary.json',{'selected':len(targets),'accepted':sum(r['label'] is not None for r in new),'pending':sum(r['label'] is None for r in new),'class_agreement':sum(decisions['A'][s]['label']==decisions['B'][s]['label'] for s in targets),'ambiguity_agreement':sum(decisions['A'][s]['ambiguity']==decisions['B'][s]['ambiguity'] for s in targets),'isolation':'Two fresh agent contexts, only guide/input; same model, shared filesystem; no expert independence','prior_accepted_reused':29,'new_sources':0})
    return new

def canonical(additional):
    snapshot_path='outputs/corpus-snapshot-v4/reviewed-export.json'
    snapshot=read(ROOT/snapshot_path)
    v3=read(ROOT/'outputs/corpus-snapshot-v3/reviewed-export.json')
    identity={r['source']:r for r in csv.DictReader((ROOT/'artifacts/beto-v2/corpus/class-work-author-format-v2.csv').open(encoding='utf-8'))}
    meta=v3['dataset']['source_registry']
    groups=read(ROOT/'artifacts/beto-v2/corpus/source-groups-v2.json')['groups']
    reserved=read(ROOT/'artifacts/beto-v2/corpus/reserved-evaluation-sources-v2.json')
    reserved_ids={r['source_id'] for r in reserved['sources']}
    # Conservative linked-document blocks, not assertions of text identity.
    links=[('historical-bas adre-hampe'.replace(' ',''),['747ca90f-92fc-4d19-aec4-6dfc34c2917e','9f60a031-0183-478c-a1f8-a3bdd37d7b0b','S15'],'Basadre/Hampe documented relationship; S15 explicitly quotes the same multi-volume Basadre work. Conservative block.'),
           ('historical-ophelan-huamanga',['0ea45102-057d-4bff-b527-f36326f66d33','9fecbe5a-9fb2-4002-a088-8a2810db938e'],'Existing documentary review identifies use of the exact O Phelan work in Huamanga; inherit whole block.'),
           ('historical-fonseca-hunefeldt',['e32181bc-41d0-4400-a76d-eb11fc88bf71','7ef1a1d4-97c6-55cf-990b-3a7b1fbb0f9d','S17'],'Existing Fonseca/Hunefeldt dependency; S17 grouped conservatively with the related slavery evidence, not asserted to be the same essay.'),
           ('callao-naval-1820',['S03','S06'],'Conservative same-episode block for overlapping Callao naval events; distinct articles retained in provenance.')]
    family={s:g for g,ss,_ in links for s in ss}
    items=[];pending=[];relations=[];works={};seen={}
    for i,r in enumerate(snapshot['items']):
        if r['split']!='train':continue
        sid=r['resourceId'];m=meta.get(sid,{})
        title=m.get('title') or identity.get(sid,{}).get('work','UNKNOWN')
        fid=family.get(sid,'work-'+sid)
        row={**r,'segment_id':f'historical-v4-{i:04}','source_id':sid,'family_id':fid,'role':'historical_train','text_sha256':hashlib.sha256(r['text'].encode()).hexdigest(),'provenance':{'snapshot':snapshot_path,'snapshot_index':i,'row_mapping':'outputs/corpus-snapshot-v4/row-mapping.json','change_archive':'outputs/corpus-snapshot-v4/originals-and-decisions.json','earlier_archive':'outputs/corpus-snapshot-v3/replacement-archive.json'},'annotation_origin':'historical reviewed snapshot; includes prior AI-assisted revisions; not uniform expert gold','training_eligible':False}
        if title=='UNKNOWN':
            row.update(role='pending',eligibility_reason='Documentary work identity unresolved; not merely resourceId');pending.append(row);continue
        assert r['label'] in LABELS and len(r['text'].strip())>0 and sid not in reserved_ids
        k=norm(r['text'])
        if k in seen:
            relations.append({'active_id':seen[k]['segment_id'],'inactive_id':row['segment_id'],'kind':'normalized_duplicate','same_label':r['label']==seen[k]['label']});continue
        row.update(training_eligible=True,eligibility_reason='Known seven-class label; reviewed-v4 survivor after quarantines; original train only; resolved work identity; no reserved family; canonical text unique. Historical extraction quality inherited, not recertified as flawless.')
        seen[k]=row;items.append(row);works[sid]={'title':title,'family_id':fid,'identity_evidence':m or identity.get(sid)}
    for r in read(ROOT/'outputs/beto-v2/pilot/pilot-annotated.json')['items']+additional:
        sid=r['source_id'];g=next(g for g in groups if sid in g['source_ids'])
        assert sid not in reserved_ids and g['role']=='annotation_pool'
        row={**r,'family_id':family.get(sid,r['family_id']),'original_family_id':r['family_id'],'role':'new_AI','text_sha256':hashlib.sha256(r['text'].encode()).hexdigest(),'training_eligible':False,'provenance':{'candidate':'outputs/beto-v2/pilot/annotation-candidates-final.jsonl','candidate_id':r['segment_id'],'source_sha256':r['source_sha256'],'adjudication':'outputs/beto-v2/first-training/adjudication.json' if r in additional else 'outputs/beto-v2/pilot/adjudication.json'}}
        if row['label'] is None:row['role']='pending';pending.append(row);continue
        assert row['label'] in LABELS and not row['quality_flags'] and row['annotation_status']=='accepted_AI_assisted' and row['pages_exact']
        assert filehash(ROOT/'outputs/beto-v2/corpus'/sid/'source.pdf')==r['source_sha256']
        assert norm(row['text']) not in seen
        row.update(training_eligible=True,eligibility_reason='Two isolated AI passes + explicit adjudication; readable or visual correction; exact pages/source hash; development family; no duplicate alternative active.')
        seen[norm(row['text'])]=row;items.append(row);works[sid]={'title':g['original_work'],'family_id':row['family_id'],'identity_evidence':'artifacts/beto-v2/corpus/source-groups-v2.json'}
    # Only one active version among any established candidate overlap pair.
    alerts=read(ROOT/'outputs/beto-v2/pilot/duplication-final-recovered.json')['alerts']
    active={r['segment_id'] for r in items}
    for a in alerts:
        assert not (a['candidate_id'] in active and a['other_id'] in active),'Active alternatives overlap'
        relations.append({**a,'candidate_active':a['candidate_id'] in active,'other_active':a['other_id'] in active})
    # Near duplicate screen limited to the canonical active set, no global re-audit.
    from sklearn.feature_extraction.text import TfidfVectorizer
    x=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=60000).fit_transform([norm(r['text']) for r in items])
    sim=(x@x.T).tocoo();removed=set()
    for i,j,v in zip(sim.row,sim.col,sim.data):
        if i>=j or v<.95:continue
        if items[i]['family_id']!=items[j]['family_id']:raise ValueError('Unresolved cross-family near duplicate')
        if items[i]['label']!=items[j]['label']:raise ValueError('Unresolved duplicate label conflict')
        if i not in removed:removed.add(j);relations.append({'active_id':items[i]['segment_id'],'inactive_id':items[j]['segment_id'],'kind':'near_duplicate_same_family','cosine':float(v)})
    inactive=[{**r,'training_eligible':False,'role':'inactive_alternative'} for i,r in enumerate(items) if i in removed]
    items=[r for i,r in enumerate(items) if i not in removed]
    save(OUT/'canonical-dataset.json',{'labels':LABELS,'items':items,'pending':pending,'inactive':inactive,'relations':relations,'historical_evaluations':{'role':'historical_evaluation_not_used','snapshot':snapshot_path,'splits':['val','test'],'counts':{'val':81,'test':137},'other_manifests':['artifacts/datasets/external-development-v1.json','artifacts/datasets/evaluation-pilot-v2.json'],'new_external_test':False},'reserved_final':{'role':'reserved_no_content_read','manifest':'artifacts/beto-v2/corpus/reserved-evaluation-sources-v2.json','source_ids':sorted(reserved_ids)},'version_policy':'Only reviewed v4 original-train survivors + pilot and this batch. Earlier snapshots are lineage, never concatenated.'})
    save(ART/'families.json',{'works':works,'conservative_links':[{'family_id':g,'source_ids':ss,'rationale':why} for g,ss,why in links],'limits':'Conservative documentary blocks, not proof of independent authors or exhaustive primary-source independence.'})
    return items

def freeze():
    from sklearn.model_selection import GroupKFold
    from transformers import AutoTokenizer
    from huggingface_hub.constants import HF_HUB_CACHE
    import torch
    assert not (ART/'protocol.json').exists()
    additional=read(OUT/'additional-annotated.json')['items'] if (OUT/'additional-annotated.json').exists() else annotations()
    rows=read(OUT/'canonical-dataset.json')['items'] if (OUT/'canonical-dataset.json').exists() else canonical(additional)
    tok=AutoTokenizer.from_pretrained(BASE,revision=REV,local_files_only=True)
    lengths=[len(tok(r['text'],truncation=False)['input_ids']) for r in rows]
    stats={'n':len(lengths),'min':min(lengths),'max':max(lengths),'quantiles':dict(zip(['p50','p90','p95','p99'],__import__('numpy').quantile(lengths,[.5,.9,.95,.99]).tolist())),'above_384':sum(n>384 for n in lengths),'lost_tokens_384':sum(max(0,n-384) for n in lengths)}
    if not (ART/'token-lengths.json').exists():save(ART/'token-lengths.json',{'summary':stats,'items':[{'segment_id':r['segment_id'],'tokens':n} for r,n in zip(rows,lengths)]})
    folds=[]
    historical=[r for r in rows if r['role']=='historical_train']
    assignment={}
    for fold,(_,held) in enumerate(GroupKFold(n_splits=3).split(historical,groups=[r['family_id'] for r in historical])):
        for i in held:assignment[historical[i]['family_id']]=fold
    new_counts=[sum(r['role']=='new_AI' and assignment.get(r['family_id'])==f for r in rows) for f in range(3)]
    unassigned=Counter(r['family_id'] for r in rows if r['family_id'] not in assignment)
    for family,count in sorted(unassigned.items(),key=lambda x:(-x[1],x[0])):
        f=min(range(3),key=lambda f:(new_counts[f],f));assignment[family]=f;new_counts[f]+=count
    for n in range(1,4):
        va=[i for i,r in enumerate(rows) if assignment[r['family_id']]==n-1]
        tr=[i for i,r in enumerate(rows) if assignment[r['family_id']]!=n-1]
        train_b=[rows[i] for i in tr];train_a=[r for r in train_b if r['role']=='historical_train'];val=[rows[i] for i in va]
        validate(train_a,val);validate(train_b,val)
        assert any(r['role']=='new_AI' for r in val) and any(r['role']=='historical_train' for r in val)
        folds.append({'id':f'fold-{n}','train_A':[r['segment_id'] for r in train_a],'train_B':[r['segment_id'] for r in train_b],'validation':[r['segment_id'] for r in val],'validation_families':sorted({r['family_id'] for r in val}),'counts':{name:{l:sum(r['label']==l for r in subset) for l in LABELS} for name,subset in [('train_A',train_a),('train_B',train_b),('validation_historical',[r for r in val if r['role']=='historical_train']),('validation_new_AI',[r for r in val if r['role']=='new_AI'])]}})
    base=Path(HF_HUB_CACHE)/('models--'+BASE.replace('/','--'))/'snapshots'/REV
    paths=['outputs/beto-v2/first-training/canonical-dataset.json','outputs/beto-v2/first-training/annotation-input.json','outputs/beto-v2/first-training/pass-a.json','outputs/beto-v2/first-training/pass-b.json','outputs/beto-v2/first-training/adjudication.json','outputs/corpus-snapshot-v4/reviewed-export.json','outputs/corpus-snapshot-v4/originals-and-decisions.json','outputs/corpus-snapshot-v4/row-mapping.json','outputs/corpus-snapshot-v3/replacement-archive.json','docs/guia-etiquetado-1780-1842.md','docs/beto-v2/guia-etiquetado-v2.md','scripts/run_beto_first_training_v2.py','scripts/freeze_beto_first_training_v2.py','scripts/beto_effective_batch_loss.py','artifacts/beto-v2/first-training/preflight.json','artifacts/beto-v2/corpus/reserved-evaluation-sources-v2.json','artifacts/beto-v2/first-training/families.json','artifacts/beto-v2/first-training/guide-compatibility.json']
    protocol={'created_at_utc':datetime.now(timezone.utc).isoformat(),'status':'frozen_before_any_classifier_fit','fold_rule':'GroupKFold(3), deterministic balance by family row count, no predictions used; original historical evaluation rows excluded','folds':folds,'labels':LABELS,'base_model':BASE,'revision':REV,'seed':42,'max_length':384,'length_reason':'Observed canonical token distribution; 384 on 4GB GPU with microbatch2 and checkpointing, established feasible hardware profile. One common length, no search.','token_summary':stats,'recipe':{'learning_rate':2e-5,'epochs':4,'microbatch':2,'gradient_accumulation':8,'effective_batch':16,'weighting':'inverse frequency per condition train','loss':'CE sum per microbatch divided by sum of target weights across actual effective batch','optimizer':'AdamW weight_decay .01','scheduler':'linear warmup 10% (min1), linear decay; scheduler advances only successful AMP steps','clip_norm':1.,'precision':'CUDA fp16 autocast + GradScaler','gradient_checkpointing':True,'selection':'maximum combined validation macro F1 over seven classes; ties earliest epoch; no early stopping','epoch_shuffle_seed':'42+epoch; model initialization seed42','resume':'epoch boundary saves optimizer/model/scaler/scheduler/Python/NumPy/torch/CUDA RNG; same dataset and protocol required'},'budget':{'full_beto_runs':6,'conditions':['A','B'],'folds':3,'extra_seeds':0},'baselines':{'majority':'train most frequent, alphabetical tie','tfidf':'word1-2, min_df2, max_features50000, sublinear_tf, unicode accents; LogisticRegression C4 balanced lbfgs max_iter2000 seed42; both A/B'},'primary':'mean across folds of combined seven-class macro F1 B-A; report historical and AI subsets separately','limits':'Exploratory one seed, three dependent development folds, checkpoint selection on the reported development rows; not unbiased test estimate or optimal model proof. Annotation AI assisted.','input_hashes':{s:filehash(ROOT/s) for s in paths},'base_hashes':{s:filehash(base/s) for s in ['config.json','pytorch_model.bin','special_tokens_map.json','tokenizer.json','tokenizer_config.json','vocab.txt']},'versions':{p:importlib.metadata.version(p) for p in ['torch','transformers','tokenizers','numpy','scikit-learn','scipy','safetensors','huggingface-hub']},'python':sys.version,'hardware':{'cuda_available':torch.cuda.is_available(),'gpu':torch.cuda.get_device_name(),'memory_bytes':torch.cuda.get_device_properties(0).total_memory}}
    protocol['fold_rule']='GroupKFold(3) on historical families by row count; already-linked new rows inherit family fold; new-only families assigned decreasing size to fold with fewest AI rows (fold ID tie). No labels or predictions used for assignment. All train classes validated, no performance-based retries.'
    save(ART/'protocol.json',protocol)
    print(json.dumps({'rows':len(rows),'roles':dict(Counter(r['role'] for r in rows)),'folds':[{'id':f['id'],'A':len(f['train_A']),'B':len(f['train_B']),'val':len(f['validation']),'families':f['validation_families']} for f in folds],'tokens':stats},ensure_ascii=False))

if __name__=='__main__':freeze()
