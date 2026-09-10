"""One frozen class-weight contrast, at most nine new BETO trajectories."""
import argparse
import ast
from collections import Counter
from run_beto_first_training_v2 import *

WART=ROOT/'artifacts/beto-v2/class-weights'
WOUT=ROOT/'outputs/beto-v2/class-weights'
SEEDS=(42,43,44)

def persist(path,value):
    if path.exists():
        if read(path)!=value:raise ValueError('Existing identity differs: '+str(path))
    else:save(path,value)

def old_path(seed,fold,c):
    return (OUT/'runs' if seed==42 else ROOT/'outputs/beto-v2/stability'/f'seed-{seed}')/(fold+'-'+c)

def weight_vector(rows):
    return [len(rows)/(7*sum(r['label']==l for r in rows)) for l in LABELS]

def preflight():
    import torch
    from beto_effective_batch_loss import accumulation_batches
    p,byid=inputs()
    assert len(byid)==591 and p['labels']==LABELS and p['revision']==REV and p['max_length']==384
    sm=read(ROOT/'artifacts/beto-v2/stability/protocol.json')
    archived=ROOT/'artifacts/beto-v2/stability/runner-stability-original.py'
    assert filehash(archived)==sm['runner_sha256']
    # Only the weight-source branch is permitted to change the training function.
    old=archived.read_text(encoding='utf-8')
    expected=old.replace('def train_run(train,val,dest,protocol):','def train_run(train,val,dest,protocol,*,weight_rows=None):').replace(
        "    weights=torch.tensor([len(train)/(7*sum(r['label']==l for r in train)) for l in LABELS],device='cuda')",
        "    weight_train=train if weight_rows is None else weight_rows\n    if weight_rows is not None:\n        if protocol['execution']['weight_source']!='train_A' or fingerprint(weight_rows)!=protocol['execution']['weight_rows_hash']:\n            raise ValueError('Class weight source identity mismatch')\n        validate(weight_train,val)\n    weights=torch.tensor([len(weight_train)/(7*sum(r['label']==l for r in weight_train)) for l in LABELS],device='cuda')")
    def fn(src,name):return ast.dump(next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name==name))
    current=(ROOT/'scripts/run_beto_first_training_v2.py').read_text(encoding='utf-8')
    for name in ('train_run','loader','predict','metrics','subsets','validate','mapping'):
        assert fn(expected,name)==fn(current,name),name
    folds=[];verified={}
    for fold in p['folds']:
        val=[byid[i] for i in fold['validation']]
        trains={c:[byid[i] for i in fold['train_'+c]] for c in ('A','B')}
        for t in trains.values():validate(t,val)
        counts={c:[sum(r['label']==l for r in t) for l in LABELS] for c,t in trains.items()}
        weights={c:weight_vector(t) for c,t in trains.items()}
        for c in ('A','B'):assert dict(zip(LABELS,counts[c]))==fold['counts']['train_'+c]
        # Exact integer test: inverse-frequency vectors proportional iff counts proportional.
        equivalent=all(counts['A'][i]*counts['B'][0]==counts['B'][i]*counts['A'][0] for i in range(7))
        checks=[]
        for c in ('A','B'):
            w=torch.tensor(weights[c],dtype=torch.float64)
            y=torch.tensor([0,0,1,2,3,4,5,6,6,2,1,0,5,6,4,3,2,6,1])
            source=torch.arange(len(y)*7,dtype=torch.float64).reshape(-1,7).sin()
            x=source.clone().requires_grad_();ref=source.clone().requires_grad_()
            data=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(torch.arange(len(y)),y),batch_size=2)
            for _,batch,denom in accumulation_batches(data,8,w):
                (torch.nn.functional.cross_entropy(x[batch[0]],batch[-1],weight=w,reduction='sum')/denom).backward()
            for start in range(0,len(y),16):
                torch.nn.functional.cross_entropy(ref[start:start+16],y[start:start+16],weight=w).backward()
            torch.testing.assert_close(x.grad,ref.grad,atol=1e-12,rtol=1e-12)
            checks.append(c+': accumulated gradients match full effective batches including partial group')
        for seed in SEEDS:
            for c in ('A','B'):
                dest=old_path(seed,fold['id'],c)
                config=p if seed==42 else read(dest/'config.json')
                if seed!=42:
                    assert config=={**p,'execution':{'seed':seed,'fold':fold['id'],'condition':c,'train_rows_hash':fingerprint(trains[c]),'validation_rows_hash':fingerprint(val),'stability_manifest_hash':fingerprint(sm)}}
                r=verify_result(dest,config,val)
                assert r['class_weights']==torch.tensor(weights[c],dtype=torch.float32).tolist()
                assert r['steps_per_epoch']==math.ceil(len(trains[c])/16)
                assert len(r['history'])==4 and all(h['optimizer_updates']+h['amp_skips']==r['steps_per_epoch'] for h in r['history'])
                assert r['best_epoch']==max(r['history'],key=lambda h:h['f1_macro'])['epoch']
                assert r['metrics']==r['history'][r['best_epoch']-1]['metrics']
                verified[f'{seed}-{fold["id"]}-{c}']={'result_sha256':filehash(dest/'result.json'),'config_hash':fingerprint(config)}
        folds.append({'fold':fold['id'],'counts':counts,'weights_float64':weights,'weights_float32':{c:torch.tensor(w,dtype=torch.float32).tolist() for c,w in weights.items()},'A_over_B':[a/b for a,b in zip(weights['A'],weights['B'])],'equivalent_under_weighted_mean':equivalent,'train_A_hash':fingerprint(trains['A']),'train_B_hash':fingerprint(trains['B']),'validation_hash':fingerprint(val),'planned_updates':4*math.ceil(len(trains['B'])/16),'checks':checks})
    manifest={'labels':LABELS,'label2id':dict(zip(LABELS,range(7))),'condition':'B_weights_A','seeds':list(SEEDS),'maximum_new_runs':9,'original_protocol_hash':fingerprint(p),'stability_manifest_hash':fingerprint(sm),'runner_sha256':filehash(ROOT/'scripts/run_beto_first_training_v2.py'),'orchestrator_sha256':filehash(__file__),'folds':folds,'verified_references':verified,'training_contract':'AST identical except explicit weight source; seed before model initialization; unchanged ordered B rows and seed+epoch shuffle','loss':'sum weighted CE / sum target weights over actual accumulation group','checkpoint_initialization':'BETO base at frozen revision, never trained A parameters'}
    persist(WART/'protocol.json',manifest)
    print('Preflight verified 18 references; weights equivalent:',[f['equivalent_under_weighted_mean'] for f in folds],flush=True)
    return p,byid,manifest

def run_weights(seed):
    assert seed in SEEDS
    p,byid,m=preflight()
    for fold,fm in zip(p['folds'],m['folds']):
        if fm['equivalent_under_weighted_mean']:
            print('Equivalent weights; no redundant fit for '+fold['id'],flush=True);continue
        train=[byid[i] for i in fold['train_B']];val=[byid[i] for i in fold['validation']];wr=[byid[i] for i in fold['train_A']]
        config={**p,'execution':{'seed':seed,'fold':fold['id'],'condition':'B_weights_A','train_rows_hash':fingerprint(train),'validation_rows_hash':fingerprint(val),'weight_source':'train_A','weight_rows_hash':fingerprint(wr),'weights':fm['weights_float32']['A'],'planned_updates':fm['planned_updates'],'class_weights_manifest_hash':fingerprint(m)}}
        dest=WOUT/f'seed-{seed}'/(fold['id']+'-B_weights_A')
        persist(dest/'config.json',config)
        if not (dest/'result.json').exists():train_run(train,val,dest,config,weight_rows=wr)
        r=verify_result(dest,config,val)
        assert r['class_weights']==fm['weights_float32']['A']
        assert r['steps_per_epoch']*4==fm['planned_updates']
        assert sum(h['optimizer_updates']+h['amp_skips'] for h in r['history'])==fm['planned_updates']
        print('Verified '+str(dest),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['preflight','run']);parser.add_argument('--seed',type=int,choices=SEEDS)
    args=parser.parse_args()
    if args.command=='preflight':preflight()
    else:
        for seed in (SEEDS if args.seed is None else [args.seed]):run_weights(seed)
