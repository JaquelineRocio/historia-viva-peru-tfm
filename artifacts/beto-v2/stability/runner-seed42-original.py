"""Isolated, frozen six-run experiment. Production trainers are not imported."""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import math
import os
import random
import sys
import time
from pathlib import Path

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/beto-v2/first-training'
ART = ROOT/'artifacts/beto-v2/first-training'
LABELS = ['campanias_conflictos_militares','contexto_colonial_antecedentes','crisis_ideas_emancipadoras','liderazgos_diplomacia_proyectos','no_relevante','organizacion_consecuencias_republicanas','participacion_social_regional']
BASE = 'dccuchile/bert-base-spanish-wwm-cased'
REV = 'c4d86612f51b4f46759c8390d1798c2febe71b93'

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def fingerprint(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def filehash(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)

def validate(train,val):
    if not train or not val: raise ValueError('Missing train/validation; no fallback allowed')
    if {r['label'] for r in train} != set(LABELS): raise ValueError('Train must contain all seven classes')
    if any(r['label'] not in LABELS for r in val): raise ValueError('Unknown validation label')
    if {r['family_id'] for r in train}&{r['family_id'] for r in val}: raise ValueError('Family leakage')
    if {r['text_sha256'] for r in train}&{r['text_sha256'] for r in val}: raise ValueError('Text leakage')
    if any(not r['training_eligible'] or r['role'] not in ('historical_train','new_AI') for r in train+val): raise ValueError('Ineligible row')

def mapping(config):
    if config.label2id != dict(zip(LABELS,range(7))) or {int(k):v for k,v in config.id2label.items()} != dict(enumerate(LABELS)):
        raise ValueError('Checkpoint label mapping mismatch')

def metrics(rows,pred):
    from sklearn.metrics import classification_report,confusion_matrix,f1_score,accuracy_score
    if len(rows)!=len(pred): raise ValueError('Prediction alignment')
    if not rows:return {'n':0,'f1_macro':None,'per_class':{l:{'precision':0,'recall':0,'f1-score':0,'support':0} for l in LABELS}}
    truth=[r['label'] for r in rows]
    return {'n':len(rows),'f1_macro':f1_score(truth,pred,labels=LABELS,average='macro',zero_division=0),'accuracy':accuracy_score(truth,pred),'per_class':{l:v for l,v in classification_report(truth,pred,labels=LABELS,output_dict=True,zero_division=0).items() if l in LABELS},'confusion_matrix':confusion_matrix(truth,pred,labels=LABELS).tolist()}

def subsets(rows,pred):
    return {name:metrics([r for r in rows if role is None or r['role']==role],[v for r,v in zip(rows,pred) if role is None or r['role']==role]) for name,role in [('combined',None),('historical','historical_train'),('new_AI','new_AI')]}

def loader(rows,tok,length,shuffle=False,seed=42):
    import torch
    encoded=tok([r['text'] for r in rows],padding='max_length',truncation=True,max_length=length,return_tensors='pt')
    keys=list(encoded)
    data=torch.utils.data.TensorDataset(*encoded.values(),torch.tensor([LABELS.index(r['label']) for r in rows]))
    return torch.utils.data.DataLoader(data,batch_size=2,shuffle=shuffle,generator=torch.Generator().manual_seed(seed),num_workers=0),keys

def predict(model,batches,keys):
    import torch
    mapping(model.config);model.eval();pred=[]
    with torch.inference_mode():
        for batch in batches:
            with torch.autocast('cuda',dtype=torch.float16):
                logits=model(**{k:batch[i].cuda() for i,k in enumerate(keys)}).logits
            pred += [LABELS[i] for i in logits.argmax(-1).cpu().tolist()]
    return pred

def train_run(train,val,dest,protocol):
    import numpy as np
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification,set_seed
    from beto_effective_batch_loss import accumulation_batches
    validate(train,val)
    if not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable; frozen protocol can resume on compatible GPU')
    set_seed(42);torch.set_num_threads(4)
    tok=AutoTokenizer.from_pretrained(BASE,revision=REV,local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(BASE,revision=REV,local_files_only=True,use_safetensors=False,num_labels=7,id2label=dict(enumerate(LABELS)),label2id=dict(zip(LABELS,range(7)))).cuda()
    mapping(model.config)
    if model.config._commit_hash!=REV:raise ValueError('Base revision mismatch')
    model.gradient_checkpointing_enable()
    val_loader,keys=loader(val,tok,protocol['max_length'])
    weights=torch.tensor([len(train)/(7*sum(r['label']==l for r in train)) for l in LABELS],device='cuda')
    opt=torch.optim.AdamW(model.parameters(),lr=2e-5,weight_decay=.01)
    steps=math.ceil(len(train)/16);total=steps*4;warmup=max(1,int(total*.1))
    scheduler=torch.optim.lr_scheduler.LambdaLR(opt,lambda s:min((s+1)/warmup,max(0.,(total-s)/max(1,total-warmup))))
    scaler=torch.amp.GradScaler('cuda')
    dest.mkdir(parents=True,exist_ok=True)
    history=[];best=-1.;best_epoch=0;best_pred=[];seconds=0.;start_epoch=1
    resumes=sorted(dest.glob('resume-epoch-*.pt'))
    if resumes:
        state=torch.load(resumes[-1],map_location='cpu',weights_only=False) # own local state, never external pickle
        if state['protocol_hash']!=fingerprint(protocol):raise ValueError('Resume protocol differs')
        model.load_state_dict(state['model']);opt.load_state_dict(state['optimizer']);scheduler.load_state_dict(state['scheduler']);scaler.load_state_dict(state['scaler'])
        random.setstate(state['python_rng']);np.random.set_state(state['numpy_rng']);torch.set_rng_state(state['torch_rng']);torch.cuda.set_rng_state_all(state['cuda_rng'])
        history=state['history'];best=state['best'];best_epoch=state['best_epoch'];best_pred=state['best_pred'];seconds=state['seconds'];start_epoch=state['epoch']+1
        del state
    started=time.perf_counter()
    for epoch in range(start_epoch,5):
        train_loader,_=loader(train,tok,protocol['max_length'],True,42+epoch)
        model.train();opt.zero_grad(set_to_none=True);loss_sum=0.;denom_sum=0.;updates=0;skips=0
        for step,batch,denominator in accumulation_batches(train_loader,8,weights):
            targets=batch[-1].cuda()
            with torch.autocast('cuda',dtype=torch.float16):
                logits=model(**{k:batch[i].cuda() for i,k in enumerate(keys)}).logits
                numerator=torch.nn.functional.cross_entropy(logits,targets,weight=weights,reduction='sum')
                loss=numerator/denominator
            scaler.scale(loss).backward();loss_sum+=numerator.item();denom_sum+=weights[targets].sum().item()
            if (step+1)%8==0 or step+1==len(train_loader):
                scaler.unscale_(opt);torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
                old=scaler.get_scale();scaler.step(opt);scaler.update()
                if scaler.get_scale()>=old:scheduler.step();updates+=1
                else:skips+=1
                opt.zero_grad(set_to_none=True)
            if (step+1)%50==0:print(f'{dest.name}: epoch {epoch} microbatch {step+1}/{len(train_loader)}',flush=True)
        pred=predict(model,val_loader,keys);score=metrics(val,pred)['f1_macro']
        history.append({'epoch':epoch,'f1_macro':score,'metrics':subsets(val,pred),'weighted_train_loss':loss_sum/denom_sum,'optimizer_updates':updates,'amp_skips':skips,'elapsed_seconds':seconds+time.perf_counter()-started})
        if score>best:
            best=score;best_epoch=epoch;best_pred=pred
            checkpoint=dest/f'checkpoint-{epoch}'
            model.save_pretrained(checkpoint,safe_serialization=True);tok.save_pretrained(checkpoint)
            save(checkpoint/'labels.json',{'labels':LABELS,'max_length':protocol['max_length'],'base':BASE,'revision':REV})
        state={'model':model.state_dict(),'optimizer':opt.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),'epoch':epoch,'history':history,'best':best,'best_epoch':best_epoch,'best_pred':best_pred,'seconds':seconds+time.perf_counter()-started,'protocol_hash':fingerprint(protocol),'python_rng':random.getstate(),'numpy_rng':np.random.get_state(),'torch_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state_all()}
        tmp=dest/f'resume-epoch-{epoch}.pt.tmp';torch.save(state,tmp);tmp.replace(dest/f'resume-epoch-{epoch}.pt');del state
        print(f'{dest.name}: epoch {epoch} F1(7)={score:.6f}',flush=True)
    seconds+=time.perf_counter()-started
    checkpoint=dest/f'checkpoint-{best_epoch}'
    del model,opt,scaler;gc.collect();torch.cuda.empty_cache()
    metadata=read(checkpoint/'labels.json')
    if metadata['labels']!=LABELS or metadata['max_length']!=protocol['max_length']:raise ValueError('Saved inference config mismatch')
    reloaded=AutoModelForSequenceClassification.from_pretrained(checkpoint,local_files_only=True,use_safetensors=True).cuda()
    reloaded_tok=AutoTokenizer.from_pretrained(checkpoint,local_files_only=True)
    reloader,rekeys=loader(val,reloaded_tok,metadata['max_length'])
    check=predict(reloaded,reloader,rekeys)
    if check!=best_pred:raise ValueError('Reload predictions mismatch')
    result={'status':'complete','history':history,'best_epoch':best_epoch,'seconds':seconds,'metrics':subsets(val,check),'predictions':[{'segment_id':r['segment_id'],'family_id':r['family_id'],'role':r['role'],'truth':r['label'],'predicted':p,'text_sha256':r['text_sha256']} for r,p in zip(val,check)],'reload_predictions_identical':True,'checkpoint_hashes':{p.name:filehash(p) for p in checkpoint.iterdir() if p.is_file()},'device':torch.cuda.get_device_name(),'steps_per_epoch':steps,'warmup_steps':warmup,'class_weights':weights.cpu().tolist(),'protocol_hash':fingerprint(protocol)}
    save(dest/'result.json',result)
    del reloaded;gc.collect();torch.cuda.empty_cache()
    return result

def inputs():
    p=read(ART/'protocol.json')
    for path,h in p['input_hashes'].items():
        if filehash(ROOT/path)!=h:raise ValueError('Changed frozen input: '+path)
    for pkg,version in p['versions'].items():
        if importlib.metadata.version(pkg)!=version:raise ValueError('Environment version differs: '+pkg)
    from huggingface_hub.constants import HF_HUB_CACHE
    base=Path(HF_HUB_CACHE)/('models--'+BASE.replace('/','--'))/'snapshots'/REV
    for name,h in p['base_hashes'].items():
        if filehash(base/name)!=h:raise ValueError('Base file differs: '+name)
    rows=read(OUT/'canonical-dataset.json')['items'];byid={r['segment_id']:r for r in rows}
    return p,byid

def run():
    from collections import Counter
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from threadpoolctl import threadpool_limits
    p,byid=inputs()
    for fold in p['folds']:
        val=[byid[i] for i in fold['validation']]
        for condition in ['A','B']:
            train=[byid[i] for i in fold['train_'+condition]];validate(train,val)
            dest=OUT/'runs'/(fold['id']+'-'+condition)
            if not (dest/'baselines.json').exists():
                started=time.perf_counter()
                majority=sorted(Counter(r['label'] for r in train).items(),key=lambda z:(-z[1],z[0]))[0][0]
                model=make_pipeline(TfidfVectorizer(strip_accents='unicode',ngram_range=(1,2),min_df=2,max_features=50000,sublinear_tf=True),LogisticRegression(C=4.,class_weight='balanced',max_iter=2000,random_state=42,solver='lbfgs'))
                with threadpool_limits(limits=1):model.fit([r['text'] for r in train],[r['label'] for r in train])
                pred=model.predict([r['text'] for r in val]).tolist()
                save(dest/'baselines.json',{'tfidf':subsets(val,pred),'majority':subsets(val,[majority]*len(val)),'predictions':[{'segment_id':r['segment_id'],'truth':r['label'],'tfidf':v,'majority':majority} for r,v in zip(val,pred)],'seconds':time.perf_counter()-started})
            if not (dest/'result.json').exists(): train_run(train,val,dest,p)
            else:
                if read(dest/'result.json')['protocol_hash']!=fingerprint(p):raise ValueError('Completed result protocol mismatch')
                print('Reusing completed '+dest.name,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['run']);parser.parse_args();run()
