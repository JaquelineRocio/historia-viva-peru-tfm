"""Complete video decoding, timestamp and source registry receipts without reading S."""
import json,hashlib,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/beto-v3/phase-b-completion-01';META=ROOT/'artifacts/beto-v3/phase-b-completion-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 registry_path=META/'source-registry-final.json';archive=META/'source-registry-before-resume.json'
 if not archive.exists():archive.write_bytes(registry_path.read_bytes())
 registry=read(registry_path)
 for sid in ['N08','N07','N03']:
  folder=BASE/'new-sources'/sid;receipt=read(folder/'download.json')
  if not receipt.get('integrity_decode_ok'):continue
  if not receipt.get('video_decode_complete'):
   started=time.perf_counter()
   result=subprocess.run(['ffmpeg','-v','error','-i',str(folder/'source.mp4'),'-map','0:v:0','-f','null','-'],capture_output=True,text=True)
   receipt.update(video_decode_complete=result.returncode==0 and not result.stderr.strip(),video_decode_returncode=result.returncode,video_decode_stderr=result.stderr,video_decode_cpu_wall_seconds=time.perf_counter()-started,integrity_scope='Entire audio and video streams decoded; semantic fidelity of ASR requires reading/listening review',verified_at_utc=datetime.now(timezone.utc).isoformat())
   save(folder/'download.json',receipt)
  transcript=folder/'asr/transcription.json'
  source=next(s for s in registry['new_candidates'] if s['source_id']==sid)
  source.update(download_receipt=str((folder/'download.json').relative_to(ROOT)),download_receipt_sha256=sha(folder/'download.json'),duration_seconds=receipt['duration_seconds'],duration_provenance='Downloaded original ffprobe format.duration; not last subtitle',audio_integrity=receipt['integrity_decode_ok'],video_integrity=receipt.get('video_decode_complete',False),primary_duration_eligible=receipt['primary_duration_eligible'],status='downloaded_original_ASR_pending',training_eligible=False)
  if transcript.exists():
   t=read(transcript);cues=t['segments'];duration=receipt['duration_seconds']
   assert all(0<=c['start']<=c['end']<=duration+1 for c in cues)
   gaps=[];end=0
   for c in cues:
    if c['start']-end>15:gaps.append([end,c['start']])
    end=max(end,c['end'])
   if duration-end>15:gaps.append([end,duration])
   quality={'audio_seconds_processed':duration,'complete_audio_processed':True,'speech_transcription_completeness':'not certified; ASR timestamps are estimates','timestamp_bounds_valid':True,'gaps_over_15_seconds':gaps,'consecutive_identical_cues':[i for i in range(1,len(cues)) if cues[i]['text']==cues[i-1]['text']],'start':cues[0]['start'] if cues else None,'end':cues[-1]['end'] if cues else None}
   save(folder/'asr/quality.json',quality)
   def stamp(x):
    ms=round(x*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
   (folder/'asr/transcript.srt').write_text('\n\n'.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues,1))+'\n',encoding='utf-8')
   source.update(status='downloaded_transcribed_local_pending_final_source_admission',transcription_method='faster-whisper-small CUDA int8_float16, es, beam5, no VAD; complete audio in sequential 300s chunks',transcript=str(transcript.relative_to(ROOT)),transcript_sha256=sha(transcript),quality_receipt=str((folder/'asr/quality.json').relative_to(ROOT)),final_role='auxiliary_quarantine' if sid=='N03' else None)
  source['next_action']='Resolve remaining annotation, source relations and corpus coverage; no training admission yet'
  print(sid,round(receipt['duration_seconds'],2),receipt.get('video_decode_complete'),transcript.exists(),flush=True)
 registry['S_closed']=True;registry['new_source_relations_receipt']='artifacts/beto-v3/phase-b-completion-01/new-source-relations.json';save(registry_path,registry)
if __name__=='__main__':main()
