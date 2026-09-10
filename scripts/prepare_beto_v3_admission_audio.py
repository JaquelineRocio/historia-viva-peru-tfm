"""Decode public originals and ASR only preregistered continuous windows."""
import os, sys, json, time, subprocess, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/beto-v3/admission-01'
ART=ROOT/'artifacts/beto-v3/admission-01'
LEDGER=ROOT/'artifacts/beto-v3/budget-ledger-current.json'
sys.path.insert(0,str(ROOT/'outputs/beto-v3/asr-tools'))
os.environ['PATH']=str(ROOT/'outputs/venv-ml/Lib/site-packages/torch/lib')+os.pathsep+os.environ['PATH']
os.environ['HF_HUB_OFFLINE']='1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
def main():
    assert (ART/'sampling-plan.json').exists()
    model=None
    for sid in sys.argv[1:]:
        folder=BASE/sid; receipt=read(folder/('audio-acquisition-aac.json' if (folder/'audio-acquisition-aac.json').exists() else 'audio-acquisition-network.json'))
        source=ROOT/receipt['path']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==receipt['sha256']
        if (folder/'download.json').exists() and read(folder/'download.json')['sha256']!=receipt['sha256']:
            assert not (folder/'asr').exists(), 'Do not replace already transcribed audio'
            save(folder/'download-opus-failure.json',read(folder/'download.json'))
            (folder/'download.json').rename(folder/'download-before-aac.json')
        if not (folder/'download.json').exists():
            start=time.perf_counter()
            probe=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(source)],capture_output=True,text=True,check=True)
            info=json.loads(probe.stdout);save(folder/'ffprobe.json',info)
            decode=subprocess.run(['ffmpeg','-v','error','-i',str(source),'-map','0:a:0','-ac','1','-ar','16000','-y',str(folder/'audio.wav')],capture_output=True,text=True)
            save(folder/'download.json',{**receipt,'duration_seconds':float(info['format']['duration']),'integrity_decode_ok':decode.returncode==0 and not decode.stderr.strip(),'decode_stderr':decode.stderr,'decode_wall_seconds':time.perf_counter()-start})
        decoded=read(folder/'download.json')
        if not decoded['integrity_decode_ok']:
            print(sid,'decode failed',flush=True);continue
        duration=decoded['duration_seconds'];assert duration>=1800
        windows=[(0,375),(duration/2-187.5,375),(duration-375,375)]
        save(folder/'windows.json',{'sampling_plan_sha256':hashlib.sha256((ART/'sampling-plan.json').read_bytes()).hexdigest(),'windows':windows})
        for i,(offset,length) in enumerate(windows):
            dest=folder/f'asr/window-{i}.json'
            if dest.exists() and read(dest).get('complete'):continue
            dest.parent.mkdir(exist_ok=True)
            if model is None:
                from faster_whisper import WhisperModel
                started=time.perf_counter()
                model=WhisperModel('small',device='cuda',compute_type='int8_float16',download_root=str(ROOT/'outputs/beto-v3/asr-models'),local_files_only=True)
                elapsed=time.perf_counter()-started
                ledger=read(LEDGER);ledger['ASR_gpu_seconds']+=elapsed;save(LEDGER,ledger)
                setup_path=ART/f'asr-setup-samples-{sid}.json'
                assert not setup_path.exists(), 'Preserve prior ASR load accounting on a new attempt'
                save(setup_path,{'model':'Systran/faster-whisper-small','load_wall_seconds':elapsed,'budget_accounted':True})
            audio=dest.with_suffix('.wav')
            subprocess.run(['ffmpeg','-v','error','-ss',str(offset),'-i',str(folder/'audio.wav'),'-t',str(length),'-y',str(audio)],check=True)
            ledger=read(LEDGER);assert ledger['ASR_gpu_seconds']+1200<=28800
            ledger['ASR_gpu_seconds']+=1200;save(LEDGER,ledger)
            record={'source_id':sid,'offset_seconds':offset,'audio_seconds':length,'source_sha256':decoded['sha256'],'model':'Systran/faster-whisper-small','device':'cuda','compute_type':'int8_float16','language':'es','beam_size':5,'vad_filter':False,'condition_on_previous_text':False,'complete':False,'reserved_gpu_seconds':1200,'segments':[]}
            save(dest,record);start=time.perf_counter()
            try:
                segments,_=model.transcribe(str(audio),language='es',beam_size=5,vad_filter=False,condition_on_previous_text=False)
                for s in segments:
                    record['segments'].append({'start':offset+s.start,'end':offset+s.end,'text':s.text.strip(),'avg_logprob':s.avg_logprob,'no_speech_prob':s.no_speech_prob})
                    if time.perf_counter()-start>1200:raise RuntimeError('ASR window allocation exhausted')
                record['complete']=True
            except Exception as e:record['error']=repr(e)
            finally:
                elapsed=time.perf_counter()-start;record['wall_seconds']=elapsed
                save(dest,record);ledger=read(LEDGER);ledger['ASR_gpu_seconds']+=elapsed-1200;save(LEDGER,ledger)
            print(sid,i,record['complete'],round(elapsed,2),flush=True)
            if not record['complete']:raise RuntimeError(record['error'])
if __name__=='__main__':main()
