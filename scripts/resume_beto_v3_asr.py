"""Timed local ASR: save every 5-minute chunk; cumulative conservative GPU budget."""
import os, sys, json, time, subprocess, threading, hashlib, argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'outputs/beto-v3/asr-tools'))
os.environ['PATH']=str(ROOT/'outputs/venv-ml/Lib/site-packages/torch/lib')+os.pathsep+os.environ['PATH']
os.environ['HF_HUB_DISABLE_XET']='1'
from faster_whisper import WhisperModel
import psutil
BASE=ROOT/'outputs/beto-v3/phase-b-completion-01/new-sources'
ART=ROOT/'artifacts/beto-v3'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(p)
def main():
 global BASE
 parser=argparse.ArgumentParser()
 parser.add_argument('--base',type=Path,default=BASE)
 parser.add_argument('--sources',nargs='+',default=['N08','N07','N03'])
 args=parser.parse_args();BASE=args.base.resolve()
 assert BASE.is_relative_to(ROOT/'outputs/beto-v3')
 pending=[]
 for sid in args.sources:
  folder=BASE/sid; transcript=folder/'asr/transcription.json'
  if not transcript.exists():pending.append(sid);continue
  receipt=read(folder/'download.json');cached=read(transcript)
  chunks=list((folder/'asr').glob('chunk-*.json'))
  assert chunks and all(read(p).get('complete') and read(p).get('source_sha256')==receipt['sha256'] for p in chunks),'Changed/incomplete ASR source: inspect before resuming'
  assert cached['complete_audio_processed'] and cached['duration_seconds']==receipt['duration_seconds']
  assert cached['segments']==read(folder/'asr/cues.json')
 if not pending:
  print('All requested complete transcripts cached; no model load or GPU spend',flush=True);return
 assert read(ART/'budget-ledger-current.json')['ASR_gpu_seconds']<28740,'ASR budget exhausted'
 model_dir=ROOT/'outputs/beto-v3/asr-models'
 run_meta=ART/('phase-b-completion-01' if BASE.name=='new-sources' else BASE.name)
 run_meta.mkdir(parents=True,exist_ok=True)
 setup=run_meta/'asr-setup.json'
 if setup.exists() and not read(setup).get('budget_accounted'):
  old=read(setup);ledger=read(ART/'budget-ledger-current.json');ledger['ASR_gpu_seconds']+=old.get('load_wall_seconds',0);save(ART/'budget-ledger-current.json',ledger);old['budget_accounted']=True;save(setup,old)
 print('Loading Systran/faster-whisper-small cuda int8_float16',flush=True)
 start=time.perf_counter()
 try: model=WhisperModel('small',device='cuda',compute_type='int8_float16',download_root=str(model_dir))
 except Exception as e:
  save(setup,{'status':'blocked','error':repr(e),'wall_seconds':time.perf_counter()-start,'GPU_inference_started':False}); raise
 load_seconds=time.perf_counter()-start
 ledger=read(ART/'budget-ledger-current.json');ledger['ASR_gpu_seconds']+=load_seconds;save(ART/'budget-ledger-current.json',ledger)
 save(setup,{'status':'loaded','model':'Systran/faster-whisper-small','device':'cuda','compute_type':'int8_float16','load_wall_seconds':load_seconds,'budget_accounted':True})
 def run(folder,name,offset,duration):
  dest=folder/'asr'/f'{name}.json'
  if dest.exists() and read(dest).get('complete'):
   cached=read(dest)
   expected={'model':'Systran/faster-whisper-small','engine':'faster-whisper 1.2.1','device':'cuda','compute_type':'int8_float16','language':'es','beam_size':5,'vad_filter':False,'condition_on_previous_text':False,'offset_seconds':offset,'audio_seconds':duration,'source_sha256':read(folder/'download.json')['sha256']}
   assert all(cached.get(k)==v for k,v in expected.items()),'Changed ASR input/config: create a new version instead of overwriting reviewed text'
   return cached
  ledger=read(ART/'budget-ledger-current.json'); remaining=28800-ledger['ASR_gpu_seconds']
  if remaining<60:raise RuntimeError('ASR cumulative budget exhausted')
  audio=folder/'asr'/f'{name}.wav'; audio.parent.mkdir(exist_ok=True)
  subprocess.run(['ffmpeg','-v','error','-ss',str(offset),'-i',str(folder/'audio.wav'),'-t',str(duration),'-y',str(audio)],check=True)
  peaks={'rss_bytes':0,'gpu_device_used_mib':0}; stop=threading.Event()
  def monitor():
   while not stop.is_set():
    peaks['rss_bytes']=max(peaks['rss_bytes'],psutil.Process().memory_info().rss)
    try:
     mem=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True).strip().splitlines()[0]);peaks['gpu_device_used_mib']=max(peaks['gpu_device_used_mib'],mem)
    except Exception:pass
    stop.wait(.5)
  worker=threading.Thread(target=monitor,daemon=True);worker.start(); started=time.perf_counter()
  record={'model':'Systran/faster-whisper-small','engine':'faster-whisper 1.2.1','device':'cuda','compute_type':'int8_float16','language':'es','beam_size':5,'vad_filter':False,'condition_on_previous_text':False,'offset_seconds':offset,'audio_seconds':duration,'source_sha256':read(folder/'download.json')['sha256'],'segments':[],'complete':False}
  # Reserve elapsed allocation before launch so interrupted processes cannot reset spend.
  reservation=min(remaining, max(120,duration*3))
  ledger['ASR_gpu_seconds']+=reservation; save(ART/'budget-ledger-current.json',ledger)
  save(dest,{**record,'reserved_gpu_seconds':reservation,'status':'running'})
  try:
   segments,info=model.transcribe(str(audio),language='es',beam_size=5,vad_filter=False,condition_on_previous_text=False)
   for seg in segments:
    record['segments'].append({'start':offset+seg.start,'end':offset+seg.end,'text':seg.text.strip(),'avg_logprob':seg.avg_logprob,'no_speech_prob':seg.no_speech_prob})
    if time.perf_counter()-started>=reservation:raise RuntimeError('Chunk wall/GPU allocation exhausted')
   record['complete']=True
  except Exception as e:record['error']=repr(e)
  finally:
   elapsed=time.perf_counter()-started;stop.set();worker.join();record.update(wall_seconds=elapsed,memory_peak=peaks)
   save(dest,record);ledger=read(ART/'budget-ledger-current.json');ledger['ASR_gpu_seconds']+=elapsed-reservation;save(ART/'budget-ledger-current.json',ledger)
  print(name,record['complete'],round(elapsed,2),peaks,flush=True)
  if not record['complete']:raise RuntimeError(record['error'])
  return record
 pilot=run(ROOT/'outputs/beto-v3/phase-b-completion-01/new-sources/N08','pilot-60s',0,60)
 total=sum(read(BASE/sid/'download.json')['duration_seconds'] for sid in pending if read(BASE/sid/'download.json').get('integrity_decode_ok'))
 estimate=total*pilot['wall_seconds']/60*2
 save(run_meta/'asr-estimate.json',{'pilot_seconds':pilot['wall_seconds'],'available_audio_seconds':total,'estimated_seconds_with_2x_margin':estimate,'remaining_budget_seconds':28800-read(ART/'budget-ledger-current.json')['ASR_gpu_seconds']})
 if estimate>28800-read(ART/'budget-ledger-current.json')['ASR_gpu_seconds']:return
 for sid in pending:
  folder=BASE/sid; receipt=read(folder/'download.json')
  if not receipt.get('integrity_decode_ok'):continue
  duration=receipt['duration_seconds']; cues=[]
  for i,offset in enumerate(range(0,int(duration)+1,300)):
   if duration-offset<.05:break
   result=run(folder,f'chunk-{i:03}',offset,min(300,duration-offset));cues+=result['segments']
  save(folder/'asr/cues.json',cues)
  save(folder/'asr/transcription.json',{'source_id':sid,'complete_audio_processed':True,'duration_seconds':duration,'cues':len(cues),'reference_status':'ASR output awaiting discourse/quality/annotation review','primary_duration_eligible':receipt['primary_duration_eligible'],'segments':cues})
if __name__=='__main__':main()
