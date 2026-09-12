"""Check notebook logic without loading BETO or training any model."""
import ast
import hashlib
import json
import math
from itertools import islice
from pathlib import Path
import numpy as np
import torch

root=Path(__file__).resolve().parents[1]
folder=root/'artifacts/beto-v3/colab-multitask'
nb=json.loads((folder/'beto_multitarea_colab.ipynb').read_text(encoding='utf-8'))
code='\n'.join(c['source'] for c in nb['cells'] if c['cell_type']=='code')
tree=ast.parse(code)
ns={'torch':torch,'np':np,'math':math}
names={'EXPECTED_LABELS','FINAL_LABELS','A_LABELS','B_LABELS','FINAL_TO_ID','B_TO_ID','NR_ID','MIN_DELTA','PATIENCE'}
functions={'loss_numerators','loss_denominators','soft_gate','error_counts','EarlyStopping','validate_split','text_hash','train_epoch','smoke_update'}
ns['hashlib']=hashlib
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in node.targets):
        exec(compile(ast.Module(body=[node],type_ignores=[]),'config','exec'),ns)
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in functions:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'logic','exec'),ns)
ns['weights_A']=torch.tensor([0.7,1.3])
ns['weights_B']=torch.tensor([0.6,0.8,1.,1.2,1.4,1.6])
ns['FINAL_TO_B']=torch.tensor([ns['B_TO_ID'].get(l,-100) for l in ns['FINAL_LABELS']])
# Numerical fixtures test loss algebra only; no model, dataset or optimizer is trained.
torch.manual_seed(9)
y=torch.tensor([4,0,1,2,3,5,6,4,1,4,2,3,4,5,6,1,4,0,4])
a=torch.randn(len(y),2,requires_grad=True);b=torch.randn(len(y),6,requires_grad=True)
da,db=ns['loss_denominators'](y)
na,nb_loss=ns['loss_numerators'](a,b,y)
grad=torch.autograd.grad(nb_loss,b,retain_graph=True)[0]
assert (grad[y==4]==0).all() and (grad[y!=4]!=0).any()
_,zero=ns['loss_numerators'](a[y==4],b[y==4],y[y==4]);assert zero.item()==0
whole=na/da+nb_loss/db
pieces=[]
for start in range(0,len(y),2):
    ra,rb=ns['loss_numerators'](a[start:start+2],b[start:start+2],y[start:start+2])
    pieces.append(ra/da+rb/db)
assert torch.allclose(whole,sum(pieces),atol=1e-6)
g1=torch.autograd.grad(whole,(a,b),retain_graph=True)
g2=torch.autograd.grad(sum(pieces),(a,b))
assert all(torch.allclose(x,z,atol=1e-7) for x,z in zip(g1,g2))
p=ns['soft_gate'](a.detach().softmax(-1).numpy(),b.detach().softmax(-1).numpy())
assert np.allclose(p.sum(1),1,atol=2e-6)
assert [ns['FINAL_TO_ID'][l] for l in ns['B_LABELS']]==[1,2,0,3,5,6]
stop=ns['EarlyStopping']()
assert stop.update(.5,1)==(True,False)
assert stop.update(.50005,2)==(True,False)
assert stop.update(.50005,3)==(False,True) and stop.best_epoch==2
stop=ns['EarlyStopping']()
assert stop.update(.5,1)==(True,False)
assert stop.update(.50005,2)==(True,False)
assert stop.update(.50010,3)==(True,True)
train=[json.loads(s) for s in (root/'artifacts/beto-v3/contrastive-subset-experiment/train-experimental.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
dev=[json.loads(s) for s in (root/'artifacts/beto-v3/colab-baseline/portable/dev.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
ns['validate_split'](train,'TRAIN',758);ns['validate_split'](dev,'DEV',160)
assert not {r['id'] for r in train}&{r['id'] for r in dev}
assert code.count('AutoModel.from_pretrained(')==1
assert "score=info['metrics']['macro_f1']" in code
assert 'for seed in SEEDS:results_by_seed.append(run_seed(seed))' in code
assert 'AutoModelForSequenceClassification' not in code
assert 'add_pooling_layer=False' in code
# Exercise the exact notebook smoke and training-update code on tiny CUDA fixtures.
# No BETO weights or project data are used by this regression check.
assert torch.cuda.is_available(),'CUDA required for AMP regression'
ns.update(DEVICE=torch.device('cuda'),GRADIENT_ACCUMULATION_STEPS=8,GRAD_CLIP=1.,
          MAX_CONSECUTIVE_AMP_SKIPS=20,islice=islice)
for k in ('weights_A','weights_B','FINAL_TO_B'):ns[k]=ns[k].cuda()
class Fixture(torch.nn.Module):
    def __init__(self,persistent=False):
        super().__init__()
        self.w=torch.nn.Parameter(torch.zeros(8,device='cuda'))
        self.calls=0;self.persistent=persistent
        def hook(g):
            self.calls+=1
            return torch.full_like(g,float('inf')) if self.persistent or self.calls==1 else g
        self.w.register_hook(hook)
    def forward(self,x):
        return self.w[:2].expand(len(x),2),self.w[2:].expand(len(x),6)
loader=[{'x':torch.ones(2,1),'labels':torch.tensor([4,0])}]
for persistent in (False,True):
    model=Fixture(persistent)
    opt=torch.optim.SGD(model.parameters(),lr=.01)
    scheduler=torch.optim.lr_scheduler.LambdaLR(opt,lambda _:1.)
    scaler=torch.amp.GradScaler('cuda')
    initial=scheduler.last_epoch
    if persistent:
        try:ns['smoke_update'](model,loader,opt,scheduler,scaler)
        except RuntimeError as exc:assert 'persistentes' in str(exc)
        else:raise AssertionError('Persistent overflow not rejected')
        assert scheduler.last_epoch==initial and model.calls==20
    else:
        result=ns['smoke_update'](model,loader,opt,scheduler,scaler)
        assert model.calls==2 and result['updates']==1
        assert scheduler.last_epoch==initial+1 and scaler.get_scale()==32768.
    assert all(p.grad is None for p in model.parameters())
old=root/'artifacts/beto-v3/colab-baseline/BETO_baseline_7_clases_3_semillas.ipynb'
assert hashlib.sha256(old.read_bytes()).hexdigest()=='3f72e052011a2d1b836ca04a752019227aa031c897a3948dfd2b04154cd75c64'
report={'syntax':'passed','loss_mask_and_empty_relevant_batch':'passed',
 'smoke_amp_cuda_overflow_then_recovery':'passed','smoke_amp_cuda_persistent_overflow_rejected':'passed',
 'weighted_accumulation_value_and_gradients_with_tail':'passed','soft_gate_and_mappings':'passed',
 'early_stopping_strict_max_ties_small_improvements':'passed','frozen_train_dev_validation':'passed',
 'baseline_hash_unchanged':True,'model_training_executed':False,'BETO_inference_executed':False,
 'colab_end_to_end_executed':False,'smoke_requires_user_colab_execution':True}
(folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
