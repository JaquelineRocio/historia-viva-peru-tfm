"""Resumable acquisition of the three already registered public originals."""
import json, time, subprocess, hashlib
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/beto-v3/phase-b-completion-01/new-sources'
def save(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 for sid in ['N08','N07','N03']:
  folder=BASE/sid; target=folder/'source.mp4'; receipt=folder/'download.json'
  if receipt.exists():
   cached=json.loads(receipt.read_text())
   if cached.get('integrity_decode_ok') and target.exists() and target.stat().st_size==cached.get('bytes') and (folder/'audio.wav').exists():continue
  probe=json.loads((folder/'media-probe.json').read_text()); start=time.perf_counter()
  record={'source_id':sid,'url':probe['url'],'paid_USD':0}
  try:
   partial=folder/'source.mp4.part'; offset=partial.stat().st_size if partial.exists() else 0
   if not target.exists():
    with requests.get(probe['url'],headers={'Range':f'bytes={offset}-'} if offset else {},stream=True,timeout=(20,60)) as r:
     r.raise_for_status()
     if offset and r.status_code!=206: offset=0
     with partial.open('ab' if offset else 'wb') as f:
      for chunk in r.iter_content(1024*1024): f.write(chunk)
    partial.rename(target)
   record['bytes']=target.stat().st_size
   assert record['bytes']==int(probe['content_length'])
   h=hashlib.sha256()
   with target.open('rb') as f:
    for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
   record['sha256']=h.hexdigest()
   result=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(target)],capture_output=True,text=True,check=True)
   metadata=json.loads(result.stdout); save(folder/'ffprobe.json',metadata)
   record['duration_seconds']=float(metadata['format']['duration'])
   decode=subprocess.run(['ffmpeg','-v','error','-i',str(target),'-map','0:a:0','-ac','1','-ar','16000','-y',str(folder/'audio.wav')],capture_output=True,text=True)
   record['decode_stderr']=decode.stderr; record['integrity_decode_ok']=decode.returncode==0 and not decode.stderr.strip()
   record['integrity_scope']='Full audio decode; container streams probed, video frames not fully decoded'
   record['primary_duration_eligible']=record['duration_seconds']>=1800 and sid!='N03'
   record['relation_status']='Quarantined pending content/reproduction comparison; no split admission'
  except Exception as e: record.update(status='blocked',error=repr(e))
  record['wall_seconds']=time.perf_counter()-start; save(receipt,record); print(json.dumps(record),flush=True)
if __name__=='__main__': main()
