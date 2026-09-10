"""Acquire targeted admission audio; immutable new receipts, no annotations/ledger writes."""
import json, sys, time, subprocess, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'outputs/beto-v3/tools'))
import yt_dlp
DEST=ROOT/'artifacts/beto-v3/admission-01'
BASE=ROOT/'outputs/beto-v3/phase-b-gap-02'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 for sid in ['G13','G16','G18']:
  folder=DEST/sid;folder.mkdir(parents=True,exist_ok=True);receipt=folder/('acquisition-network-approved.json' if '--network-approved' in sys.argv else 'acquisition.json')
  if receipt.exists():continue
  meta=read(BASE/sid/'receipt.json');start=time.perf_counter();r={'source_id':sid,'url':meta['url'],'gpu_seconds':0,'paid_USD':0}
  try:
   with yt_dlp.YoutubeDL({'format':'bestaudio[ext=m4a]/bestaudio','outtmpl':str(folder/'source.%(ext)s'),'noplaylist':True,'retries':0,'extractor_retries':0,'fragment_retries':0,'socket_timeout':25,'quiet':True,'writeinfojson':True}) as y:
    info=y.extract_info(meta['url'],download=True);p=Path(y.prepare_filename(info))
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)],text=True));save(folder/'ffprobe.json',probe)
   decode=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-ac','1','-ar','16000','-y',str(folder/'audio.wav')],capture_output=True,text=True)
   r.update(status='downloaded',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),duration_seconds=float(probe['format']['duration']),integrity_decode_ok=decode.returncode==0 and not decode.stderr.strip(),decode_stderr=decode.stderr,path=str(p.relative_to(ROOT)))
  except Exception as e:r.update(status='blocked',error=repr(e))
  r['wall_seconds']=time.perf_counter()-start;save(receipt,r);print(sid,r['status'],flush=True)
if __name__=='__main__':main()
