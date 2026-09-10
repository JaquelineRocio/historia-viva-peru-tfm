"""Single public audio acquisition attempt for an explicitly registered non-reserved work."""
import json
import sys
import time
from datetime import datetime, timezone

from acquire_beto_v3 import ROOT, OUT, SOURCES, EXTRA_SOURCES, save, sha

sys.path.insert(0, str(ROOT/'outputs/beto-v3/tools'))

def main():
    import yt_dlp
    vid = 'KIZbI_9WDQA'
    assert next(r for v,r,*_ in SOURCES+EXTRA_SOURCES if v==vid) == 'T'
    folder = OUT/vid/'audio-pilot'
    folder.mkdir(parents=True,exist_ok=True)
    receipt = folder/('receipt-network-approved.json' if '--network-approved' in sys.argv else 'receipt.json')
    if receipt.exists():
        print(receipt.read_text(encoding='utf-8'))
        return
    record = {'video_id':vid,'started_at':datetime.now(timezone.utc).isoformat(),
        'purpose':'ASR pilot prerequisite; no transcription started','gpu_seconds':0}
    started=time.perf_counter()
    try:
        options={'format':'bestaudio/best','outtmpl':str(folder/'source.%(ext)s'),
            'noplaylist':True,'retries':0,'extractor_retries':0,'fragment_retries':0,'socket_timeout':25,
            'max_filesize':200_000_000,'quiet':False,'no_warnings':False}
        with yt_dlp.YoutubeDL(options) as ydl:
            info=ydl.extract_info('https://www.youtube.com/watch?v='+vid, download=True)
            filename=ydl.prepare_filename(info)
        from pathlib import Path
        record.update(status='audio_obtained',path=str(Path(filename).relative_to(ROOT)),
            sha256=sha(Path(filename)),duration_seconds=info.get('duration'))
    except Exception as exc:
        record.update(status='blocked',error_type=type(exc).__name__,error=str(exc))
    record['seconds']=time.perf_counter()-started
    save(receipt,record)
    print(json.dumps(record))

if __name__=='__main__':
    main()
