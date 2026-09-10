"""Forensic counterexamples and external-checkpoint replay; no training."""
import ast, collections, json, sys
from pathlib import Path
from audit_beto_v2 import ROOT, read, sha, save, csvsave
import torch
from sklearn.metrics import f1_score
sys.path.insert(0,str(ROOT/'apps/ml'))
from app.ml.experiment_data import validate_snapshot
from app.ml.beto_experiment import predict_beto

out=ROOT/'artifacts/beto-v2/audit'
result={'command':'outputs/venv-ml/Scripts/python.exe scripts/audit_beto_v2_checks.py','runner_sha256':sha(Path(__file__)),'checks':[]}
# Execute only split expressions from AST, not training imports/calls.
tree=ast.parse((ROOT/'apps/ml/app/ml/trainer.py').read_text(encoding='utf-8'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_run')
assigns=[n for n in fn.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['train_rows','val_rows','test_rows','metrics_split']]
for names in [('train',),('train','val')]:
    items=[{'split':n,'text':n} for n in names]; env={'items':items,'_split':lambda rows,name:[r for r in rows if r['split']==name]}
    exec(compile(ast.fix_missing_locations(ast.Module(body=assigns,type_ignores=[])),'split-only','exec'),env)
    result['checks'].append({'case':'service_missing_splits','available':names,'validation_is_train':env['val_rows'] is env['train_rows'],'test_is_validation':env['test_rows'] is env['val_rows'],'reported_split':env['metrics_split']})
nb=read(ROOT/'notebooks/train_beto_colab.ipynb');src='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code' and 'def split(name)' in ''.join(c['source']))
splitfn=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='split')
expr=splitfn.body[0].value
items=[{'split':'train'},{'split':'val'}]
actual=eval(compile(ast.Expression(expr),'notebook-split-only','eval'),{'items':items,'name':'test'})
assert actual is items
result['checks'].append({'case':'notebook_missing_test','actual_rows':['train','val'],'reported_split':'val','passed_counterexample':True})
gold=read(ROOT/'artifacts/datasets/gold-v1-source-aware.json')
try: validate_snapshot({**gold,'items':[r for r in gold['items'] if r['split']=='train']})
except ValueError as e: result['checks'].append({'case':'experiment_missing_splits_rejected','error':str(e)})
else: raise AssertionError('Experiment validator failed')
logits=torch.tensor([[2.,0.],[0.,2.],[1.,0.],[0.,1.]])
y=torch.tensor([0,1,0,0]);w=torch.tensor([1.,7.])
micro=(torch.nn.functional.cross_entropy(logits[:2],y[:2],weight=w)+torch.nn.functional.cross_entropy(logits[2:],y[2:],weight=w))/2
full=torch.nn.functional.cross_entropy(logits,y,weight=w)
assert abs(micro.item()-full.item())>1e-3
result['checks'].append({'case':'weighted_microbatch_not_equal_effective_batch','micro_loss':micro.item(),'full_loss':full.item()})
result['checks'].append({'case':'macro_label_set','seven':f1_score(['a'],['a'],labels=list('abcdefg'),average='macro',zero_division=0),'implicit':f1_score(['a'],['a'],average='macro',zero_division=0)})
# Replay original GPU fp16 experimental prediction path on the located 31 cases.
external=read(ROOT/'artifacts/datasets/external-development-v1.json'); ck=ROOT/'outputs/experiments/beto-u1/beto-lr2e5'
torch.set_num_threads(2)
pred=predict_beto(ck,external['items'],external['labels'],{'batch_size':2,'max_len':192})
old=read(ROOT/'artifacts/experiments/beto-length-v1/report.json')
assert pred==[r['before'] for r in old['per_item']]
truth=[r['label'] for r in external['items']]
result['external']={'dataset_sha256':sha(ROOT/'artifacts/datasets/external-development-v1.json'),'checkpoint':str(ck.relative_to(ROOT)),'checkpoint_sha256':sha(ck/'model.safetensors'),'n':len(pred),'correct':sum(a==b for a,b in zip(truth,pred)),'f1_macro_five':f1_score(truth,pred,labels=external['metric_labels'],average='macro',zero_division=0),'f1_macro_seven':f1_score(truth,pred,labels=external['labels'],average='macro',zero_division=0),'all_historical_predictions_reproduced':True}
csvsave(out/'predictions-external.csv',[{'id':r['id'],'truth':r['label'],'prediction':p,'source':r['resourceId']} for r,p in zip(external['items'],pred)],['id','truth','prediction','source'])
result['source_metadata']={}
snap=ROOT/'outputs/agn-snapshot-v1/maintenance/snapshot.json'
if snap.exists():
    d=read(snap)
    def walk(v):
        if isinstance(v,dict):
            if isinstance(v.get('id'),str) and any(k in v for k in ['title','author']): result['source_metadata'][v['id']]={k:v[k] for k in ['title','author','sourceType','type'] if k in v}
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(d)
result['source_metadata_evidence']=str(snap.relative_to(ROOT))
save(out/'forensic-checks.json',result)
print(json.dumps(result['external'],indent=2))
