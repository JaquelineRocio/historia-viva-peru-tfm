"""Bounded public audio retrieval for two previously registered V candidates."""
import json, sys, time, hashlib
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'outputs/beto-v3/media-tools'))
import yt_dlp

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    registry=json.loads((ROOT/'artifacts/beto-v3/recovery-01/remaining-existing-V.json').read_text(encoding='utf-8'))
    for sid in ['N01', '-Ma1tt97eFg']:
        row=next(r for r in registry['sources'] if r['source_id']==sid)
        assert row['original_proposed_role']=='V' and row['assessment']=='no_local_authentic_transcript'
        folder=ROOT/'outputs/beto-v3/admission-01'/sid
        folder.mkdir(parents=True,exist_ok=True)
        dest=folder/('audio-acquisition-aac.json' if '--aac' in sys.argv else ('audio-acquisition-network.json' if '--network-approved' in sys.argv else 'audio-acquisition.json'))
        if dest.exists():
            print(sid, 'cached', flush=True); continue
        result={'source_id':sid,'video_id':row['video_id'],'role':'V','started_at':datetime.now(timezone.utc).isoformat(),
                'annotation_inputs':0,'ASR_seconds':0,'services_paid_USD':0,'eligible_for_annotation':False}
        started=time.perf_counter()
        try:
            options={'format':'bestaudio[ext=m4a]' if '--aac' in sys.argv else 'bestaudio/best','outtmpl':str(folder/('source-aac.%(ext)s' if '--aac' in sys.argv else 'source.%(ext)s')),'noplaylist':True,'noprogress':True,
                     'retries':0,'extractor_retries':0,'fragment_retries':0,'socket_timeout':20,
                     'max_filesize':200_000_000,'quiet':True,'writeinfojson':True}
            with yt_dlp.YoutubeDL(options) as y:
                info=y.extract_info('https://www.youtube.com/watch?v='+row['video_id'],download=True)
                target=Path(y.prepare_filename(info))
            result.update(status='audio_obtained_pending_decode_and_admission',path=str(target.relative_to(ROOT)),
                          duration_seconds=info.get('duration'),sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        except Exception as exc:
            result.update(status='blocked',error_type=type(exc).__name__,error=str(exc))
        result['wall_seconds']=time.perf_counter()-started
        save(dest,result)
        print(json.dumps(result,ensure_ascii=True),flush=True)

if __name__=='__main__': main()
