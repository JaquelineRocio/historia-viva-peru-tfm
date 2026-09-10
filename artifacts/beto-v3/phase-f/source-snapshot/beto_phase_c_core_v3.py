"""Phase C core copied from the corrected V2 runner; V2 remains untouched.
Changes: configured LR/horizon, numeric resume sort, budget polling, train metrics,
and idempotent checkpoint metadata after interrupted saves. Helpers reuse V2.
"""
from run_beto_first_training_v2 import *
import shutil

_BUDGET_CHECK = lambda: None

def budget_check():
    _BUDGET_CHECK()


def predict(model,batches,keys):
    import torch
    mapping(model.config);model.eval();pred=[]
    with torch.inference_mode():
        for batch in batches:
            budget_check()
            with torch.autocast('cuda',dtype=torch.float16):
                logits=model(**{k:batch[i].cuda() for i,k in enumerate(keys)}).logits
            pred += [LABELS[i] for i in logits.argmax(-1).cpu().tolist()]
    return pred


def persist(path, value):
    if path.exists():
        if read(path) != value:
            raise ValueError('Existing metadata differs: ' + str(path))
    else:
        save(path, value)


def retain_latest(dest, epoch, best_epoch, protocol, history):
    if protocol['execution'].get('retention') != 'best_and_latest':
        return
    root = (ROOT / 'outputs/beto-v3/phase-c').resolve()
    dest = dest.resolve()
    if not dest.is_relative_to(root) or dest.parent.name not in ('seed-43', 'seed-44'):
        raise ValueError('Retention outside new D runs')
    temporary = dest / 'history.json.tmp'
    save(temporary, history)
    temporary.replace(dest / 'history.json')
    # Commit full resume first; only then discard superseded states/checkpoints.
    for path in list(dest.glob('resume-epoch-*.pt')) + list(dest.glob('checkpoint-*')):
        resolved = path.resolve()
        if resolved.parent != dest:
            raise ValueError('Unsafe retention path')
        keep = epoch if path.name.startswith('resume-') else best_epoch
        if int(path.stem.rsplit('-', 1)[1]) != keep:
            if path.is_dir():
                shutil.rmtree(resolved)
            else:
                resolved.unlink()


def validate(train, val):
    # Eligibility is established against the frozen references by the orchestrator.
    if not train or not val or {r['label'] for r in train} != set(LABELS):
        raise ValueError('Missing rows or train class')
    if any(r['label'] not in LABELS for r in val):
        raise ValueError('Unknown validation label')
    for key in ('family_id', 'source_id', 'text_sha256', 'segment_id'):
        if {r[key] for r in train} & {r[key] for r in val}:
            raise ValueError('Train/V leakage: ' + key)


def train_run(train,val,dest,protocol,*,weight_rows=None):
    import numpy as np
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification,set_seed
    from beto_effective_batch_loss import accumulation_batches
    validate(train,val)
    if not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable; frozen protocol can resume on compatible GPU')
    seed=protocol.get('execution',{}).get('seed',42)
    set_seed(seed);torch.set_num_threads(4)
    tok=AutoTokenizer.from_pretrained(BASE,revision=REV,local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(BASE,revision=REV,local_files_only=True,use_safetensors=False,num_labels=7,id2label=dict(enumerate(LABELS)),label2id=dict(zip(LABELS,range(7)))).cuda()
    mapping(model.config)
    if model.config._commit_hash!=REV:raise ValueError('Base revision mismatch')
    model.gradient_checkpointing_enable()
    val_loader,keys=loader(val,tok,protocol['max_length'])
    weight_train=train if weight_rows is None else weight_rows
    if weight_rows is not None:
        if protocol['execution']['weight_source']!='train_A' or fingerprint(weight_rows)!=protocol['execution']['weight_rows_hash']:
            raise ValueError('Class weight source identity mismatch')
        validate(weight_train,val)
    weights=torch.tensor([len(weight_train)/(7*sum(r['label']==l for r in weight_train)) for l in LABELS],device='cuda')
    opt=torch.optim.AdamW(model.parameters(),lr=protocol['execution']['lr'],weight_decay=.01)
    steps=math.ceil(len(train)/16);total=steps*protocol['execution']['epochs'];warmup=max(1,int(total*.1))
    scheduler=torch.optim.lr_scheduler.LambdaLR(opt,lambda s:min((s+1)/warmup,max(0.,(total-s)/max(1,total-warmup))))
    scaler=torch.amp.GradScaler('cuda')
    dest.mkdir(parents=True,exist_ok=True)
    history=[];best=-1.;best_epoch=0;best_pred=[];seconds=0.;start_epoch=1
    resumes=sorted(dest.glob('resume-epoch-*.pt'), key=lambda p:int(p.stem.rsplit('-',1)[1]))
    if resumes:
        state=torch.load(resumes[-1],map_location='cpu',weights_only=False) # own local state, never external pickle
        if state['protocol_hash']!=fingerprint(protocol):raise ValueError('Resume protocol differs')
        model.load_state_dict(state['model']);opt.load_state_dict(state['optimizer']);scheduler.load_state_dict(state['scheduler']);scaler.load_state_dict(state['scaler'])
        random.setstate(state['python_rng']);np.random.set_state(state['numpy_rng']);torch.set_rng_state(state['torch_rng']);torch.cuda.set_rng_state_all(state['cuda_rng'])
        history=state['history'];best=state['best'];best_epoch=state['best_epoch'];best_pred=state['best_pred'];seconds=state['seconds'];start_epoch=state['epoch']+1
        del state
    started=time.perf_counter()
    for epoch in range(start_epoch,protocol['execution']['epochs']+1):
        budget_check()
        train_loader,_=loader(train,tok,protocol['max_length'],True,seed+epoch)
        model.train();opt.zero_grad(set_to_none=True);loss_sum=0.;denom_sum=0.;updates=0;skips=0
        for step,batch,denominator in accumulation_batches(train_loader,8,weights):
            budget_check()
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
        train_eval,train_keys=loader(train,tok,protocol['max_length'])
        train_metrics=metrics(train,predict(model,train_eval,train_keys))
        history.append({'train_metrics_eval':train_metrics,'epoch':epoch,'f1_macro':score,'metrics':subsets(val,pred),'weighted_train_loss':loss_sum/denom_sum,'optimizer_updates':updates,'amp_skips':skips,'elapsed_seconds':seconds+time.perf_counter()-started})
        if score>best:
            best=score;best_epoch=epoch;best_pred=pred
            checkpoint=dest/f'checkpoint-{epoch}'
            model.save_pretrained(checkpoint,safe_serialization=True);tok.save_pretrained(checkpoint)
            persist(checkpoint/'labels.json',{'labels':LABELS,'max_length':protocol['max_length'],'base':BASE,'revision':REV})
        state={'model':model.state_dict(),'optimizer':opt.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),'epoch':epoch,'history':history,'best':best,'best_epoch':best_epoch,'best_pred':best_pred,'seconds':seconds+time.perf_counter()-started,'protocol_hash':fingerprint(protocol),'python_rng':random.getstate(),'numpy_rng':np.random.get_state(),'torch_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state_all()}
        tmp=dest/f'resume-epoch-{epoch}.pt.tmp';torch.save(state,tmp);tmp.replace(dest/f'resume-epoch-{epoch}.pt');del state
        retain_latest(dest, epoch, best_epoch, protocol, history)
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
