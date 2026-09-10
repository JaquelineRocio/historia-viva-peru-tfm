"""One prospectively registered T-only comparison; reuse frozen C core and D controls."""
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/'outputs/beto-v3/phase-f/process-cache'
for key, folder in {'HF_HOME':'hf','HF_HUB_CACHE':'hf/hub','HF_DATASETS_CACHE':'datasets',
                    'TORCH_HOME':'torch','XDG_CACHE_HOME':'xdg','TEMP':'tmp','TMP':'tmp',
                    'CUDA_CACHE_PATH':'cuda','TRITON_CACHE_DIR':'triton'}.items():
    os.environ[key] = str(CACHE/folder)
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1',
                  PYTHONDONTWRITEBYTECODE='1', HF_HUB_DISABLE_TELEMETRY='1')
sys.dont_write_bytecode = True
import json
import shutil
import math
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
import run_beto_phase_c_v3 as r
A = r.ART/'phase-f'
OUT = ROOT/'outputs/beto-v3/phase-f'

def now(): return datetime.now(timezone.utc).isoformat()
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    tmp.replace(path)

def pinned(entry):
    logical = ROOT/entry['path']
    path = logical.resolve()
    r.require(path.is_relative_to(ROOT) or (logical.absolute().is_relative_to(ROOT/'outputs')
              and path.is_relative_to(Path('E:/BETO/outputs').resolve())), 'Unexpected pinned path')
    r.require(r.filehash(path)==entry['sha256'], 'Frozen bytes changed: '+str(path))
    return path
r.pinned = pinned  # Junction-aware read-only hash checking; C/D code stays intact.

def storage():
    r.require((ROOT/'outputs').resolve()==Path('E:/BETO/outputs').resolve(), 'Wrong outputs target')
    return {d:shutil.disk_usage(d)._asdict() for d in ('C:/','D:/','E:/')}

def prepare():
    disks = storage()
    r.require(disks['E:/']['free']>140*1024**3, 'Need 120 GiB estimate plus 20 GiB margin')
    r.require(min(disks[d]['free'] for d in ('C:/','D:/'))>2*1024**3, 'System disk margin')
    for key in ('HF_HOME','HF_HUB_CACHE','HF_DATASETS_CACHE','TORCH_HOME','XDG_CACHE_HOME','TEMP','TMP','CUDA_CACHE_PATH','TRITON_CACHE_DIR'):
        Path(os.environ[key]).mkdir(parents=True, exist_ok=True)
    p = r.read(r.ART/'protocol.json')
    suffix = Path('models--'+r.BASE.replace('/','--'))/'snapshots'/r.REV
    source = Path('C:/Users/JAQUELINE/.cache/huggingface/hub')/suffix
    target = Path(os.environ['HF_HUB_CACHE'])/suffix
    target.mkdir(parents=True, exist_ok=True)
    for name, digest in p['base_hashes'].items():
        r.require(r.filehash(source/name)==digest, 'Base source differs')
        if not (target/name).exists(): shutil.copy2(source/name,target/name)
        r.require(r.filehash(target/name)==digest, 'Base copy differs')
    p = r.protocol_check()
    freeze, rows = r.frozen_inputs()
    prior = r.read(r.ART/'budget-ledger-after-D.json')
    for entry in prior['attempts']: pinned(entry)
    controls = []
    for seed in (42,43,44):
        dest = r.OUT/f'seed-{seed}'/'R2'
        config = r.read(dest/'config.json')
        result = r.verify_result(dest,config,rows['V'])
        r.require(config['execution']['train_rows_hash']==r.fingerprint(rows['H']+rows['T300']), 'Control train differs')
        r.require(config['execution']['freeze_sha256']==r.filehash(r.FREEZE), 'Control freeze differs')
        r.require(len(result['history'])==20 and result['reload_predictions_identical'], 'Control incomplete')
        controls.append(dict(seed=seed,path=str((dest/'result.json').relative_to(ROOT)),sha256=r.filehash(dest/'result.json'),config_sha256=r.filehash(dest/'config.json')))
    for path in (r.ART/'development-current.json', r.ART/'budget-ledger-current.json',r.ART/'budget-ledger-after-D.json',ROOT/'docs/beto-v3/progress.md'):
        dst=A/'before'/path.name
        dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists(): shutil.copy2(path,dst)
    counts=Counter(x['label'] for x in rows['T300'])
    contract=dict(phase='F',option='transcript_only',registered_utc=now(),authorization='User explicitly extends C-D validation amendment to F before training',
        original_contract=freeze['development_contract'],freeze_sha256=r.filehash(r.FREEZE),
        scope=['F'],V_minimum_overrides={'contexto_colonial_antecedentes':23,'organizacion_consecuencias_republicanas':23},
        original_operational_goal=25,operational_goal_met=False,original_budget=p['budget'],original_success=p['evaluation']['targets'],
        labels=r.LABELS,S_closed=True,controls=controls,seeds=[42,43,44],epochs=20,scheduler_horizon_epochs=20,
        lr=2e-5,train_n=len(rows['T300']),validation_n=len(rows['V']),class_counts=counts,
        class_weights={l:len(rows['T300'])/(7*counts[l]) for l in r.LABELS},steps_per_epoch=math.ceil(len(rows['T300'])/16),
        total_step_opportunities=math.ceil(len(rows['T300'])/16)*20,warmup_steps=max(1,int(math.ceil(len(rows['T300'])/16)*20*.1)),
        selection='Mean pooled V macro F1 over all 3 best checkpoints; earliest epoch on checkpoint ties; if absolute mean difference <0.005 prefer lower cumulative measured trajectory wall cost; exact cost tie retains R2 H+T',
        uncertainty='Sample SD n-1 and paired seed deltas; per-class/work gains and losses. Seeds are not source replicates. Development V reused; no final success claim.',
        limitations='23+23 remains below 25; V 444/489 resolvable, AI-assisted not expert gold, sampled spans not full videos, 11 admitted subtitle gaps. No extension to S/final evaluation.',
        retention='Keep all newly created epoch resumes and improved checkpoints; no deletion or moving existing files',
        global_remaining_seconds=p['budget']['total_training_gpu_seconds']-prior['new_training_gpu_seconds'],
        baseline='Fit the frozen TF-IDF recipe on T only for matched context; reuse H+T baseline; no tuning')
    if not (A/'preregistration.json').exists(): write(A/'preregistration.json',contract)
    write(A/'storage-and-input-verification.json',dict(checked_utc=now(),disks=disks,junction_target=str((ROOT/'outputs').resolve()),
        estimated_max_new_bytes=120*1024**3,estimate='60 full states at <=1.5 GiB plus <=60 improved checkpoints at <=0.5 GiB, cache and metadata within 120 GiB; 20 GiB extra margin',
        C_D_expected_writes='No planned bulk writes; D scripts/audit/docs <100 MiB; bytecode disabled, all process caches/temp E. OS/other processes outside estimate.',
        process_environment={k:v for k,v in os.environ.items() if k in ('HF_HOME','HF_HUB_CACHE','HF_DATASETS_CACHE','TORCH_HOME','XDG_CACHE_HOME','TEMP','TMP','CUDA_CACHE_PATH','TRITON_CACHE_DIR','PYTHONDONTWRITEBYTECODE','HF_HUB_OFFLINE')},
        scope='F required frozen hashes, admission, partition disjointness, base files, environment, three control checkpoints and receipts. Not full migration or backup verification.',
        outputs_respaldo='Untouched; not traversed',frozen_counts={k:len(v) for k,v in rows.items()},S_content_opened=False))
    print(json.dumps(dict(preflight='passed',counts=contract['class_counts'],steps=contract['steps_per_epoch'],remaining=contract['global_remaining_seconds']),ensure_ascii=False),flush=True)

def ledger(status):
    prior=r.read(A/'before/budget-ledger-after-D.json')
    attempts=[(f,r.read(f)) for f in sorted((OUT/'attempts').glob('*.json'))]
    seconds=sum(v.get('wall_seconds',v['reserved_seconds']) for _,v in attempts)
    prior.update(new_training_trajectories=prior['new_training_trajectories']+len(list(OUT.glob('seed-*/T-only/attempt-started.json'))),
        new_training_gpu_seconds=prior['new_training_gpu_seconds']+seconds,phase_F_wall_seconds=seconds,
        accounting_method='Immutable after-D snapshot plus F receipts once each; wall includes loading/saving/reload; unsettled attempt reserves full allowance. CD unchanged.',
        phase_F_attempts=[dict(path=str(f.relative_to(ROOT)),sha256=r.filehash(f)) for f,_ in attempts],S_content_opened=False)
    write(r.ART/'budget-ledger-after-F.json',prior);write(r.ART/'budget-ledger-current.json',prior)
    state=r.read(r.ART/'development-current.json')
    state.update(status=status,updated_utc=now(),budget_ledger='artifacts/beto-v3/budget-ledger-after-F.json',phase_F_audit='artifacts/beto-v3/phase-f',S_closed=True)
    state['next_intervention']=dict(phase='F',option='transcript_only_vs_H_plus_T',executed=status=='F_complete',prospective_V_exception_scope_required=False)
    write(r.ART/'development-current.json',state)
    return prior

def run(seed):
    started=time.perf_counter()
    r.require(seed in (42,43,44),'Only registered seeds')
    contract=r.read(A/'preregistration.json')
    r.require(contract['freeze_sha256']==r.filehash(r.FREEZE),'Freeze differs')
    for entry in contract['controls']: pinned(entry)
    p=r.protocol_check(); _,rows=r.frozen_inputs()
    train,val=rows['T300'],rows['V']
    config={**p,'execution':dict(seed=seed,recipe='F-T-only-R2',lr=2e-5,epochs=20,
        train_rows_hash=r.fingerprint(train),validation_rows_hash=r.fingerprint(val),freeze_sha256=r.filehash(r.FREEZE),
        core_sha256=r.filehash(Path(r.core.__file__)),legacy_runner_sha256=r.filehash(ROOT/'scripts/run_beto_first_training_v2.py'),
        runner_sha256=r.filehash(__file__),preregistration_sha256=r.filehash(A/'preregistration.json'),retention='all_no_deletion')}
    dest=OUT/f'seed-{seed}'/'T-only'
    r.core.persist(dest/'config.json',config)
    if (dest/'result.json').exists():
        r.verify_result(dest,config,val); print('Existing complete result reused');return
    r.require(not (r.OUT/'run.lock').exists(),'C/D GPU lock exists')
    lock=OUT/'run.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    try:
        current=ledger('F_running')
        allowance=p['budget']['total_training_gpu_seconds']-current['new_training_gpu_seconds']
        r.require(allowance>180,'Global budget exhausted')
        marker=dest/'attempt-started.json'
        if marker.exists(): r.require(bool(list(dest.glob('resume-epoch-*.pt'))),'Interrupted trajectory has no resume')
        else:
            r.require(current['new_training_trajectories']<18 and len(list(OUT.glob('seed-*/T-only/attempt-started.json')))<3,'Trajectory ceiling')
            r.core.persist(marker,dict(seed=seed,config_hash=r.fingerprint(config)))
        receipt=OUT/'attempts'/(str(uuid.uuid4())+'.json')
        attempt=dict(seed=seed,recipe='F-T-only-R2',started_utc=now(),status='reserved',reserved_seconds=allowance)
        write(receipt,attempt);ledger('F_running')
        last_disk=[0.]
        def check():
            r.require(time.perf_counter()-started<allowance-120,'Global compute stop with saving margin')
            if time.perf_counter()-last_disk[0]>10:
                ds=storage();r.require(ds['E:/']['free']>20*1024**3,'E disk reserve reached')
                r.require(min(ds[d]['free'] for d in ('C:/','D:/'))>2*1024**3,'C/D reserve reached')
                last_disk[0]=time.perf_counter()
        r.core._BUDGET_CHECK=check
        # Preserve every newly produced state; original core handles checkpoint reload.
        original_retain=r.core.retain_latest
        def history_only(dest,epoch,best_epoch,protocol,history): write(dest/'history.json',history)
        r.core.retain_latest=history_only
        try:
            check();result=r.core.train_run(train,val,dest,config)
            r.verify_result(dest,config,val)
            import torch
            state=torch.load(dest/'resume-epoch-20.pt',map_location='cpu',weights_only=False)
            assert state['epoch']==20 and state['protocol_hash']==r.fingerprint(config)
            assert state['history']==result['history'] and state['best_pred']==[v['predicted'] for v in result['predictions']]
            assert all(k in state for k in ('model','optimizer','scheduler','scaler','python_rng','numpy_rng','torch_rng','cuda_rng'))
            assert state['scheduler']['last_epoch']==sum(h['optimizer_updates'] for h in result['history'])
            assert result['steps_per_epoch']==27 and result['warmup_steps']==54
            assert all(abs(w-contract['class_weights'][l])<1e-6 for w,l in zip(result['class_weights'],r.LABELS))
            del state
            write(dest/'resume-verification.json',dict(status='passed',epoch=20,full_state_loaded_cpu=True,checkpoint_reload_predictions_identical=True,power_failure_test=False))
            write(dest/'by-work.json',r.by_work(val,[v['predicted'] for v in result['predictions']]))
            attempt['status']='complete'
        except BaseException as e:
            attempt.update(status='failed_or_interrupted',error=repr(e));raise
        finally:
            attempt['wall_seconds']=time.perf_counter()-started;write(receipt,attempt)
            r.core._BUDGET_CHECK=lambda:None;r.core.retain_latest=original_retain
            ledger('F_running' if attempt['status']=='complete' else 'F_interrupted')
        print(json.dumps(dict(seed=seed,f1=result['metrics']['combined']['f1_macro'],wall=attempt['wall_seconds'])),flush=True)
    finally: lock.unlink()

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run(int(sys.argv[2]))
