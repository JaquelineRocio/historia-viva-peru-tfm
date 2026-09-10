"""Full public audio decode with cached hash/metadata receipts; no ASR spending."""
import hashlib, subprocess, time, sys
from acquire_beto_v3_gap_batch import DEST, read, save
for sid in sys.argv[1:]:
    folder=DEST/sid;source=folder/'source-aac.m4a' if (folder/'source-aac.m4a').exists() else folder/'source.webm';dest=folder/'download.json'
    if dest.exists() and read(dest).get('integrity_decode_ok'):continue
    if dest.exists():save(folder/'download-opus-failure.json',read(dest))
    start=time.perf_counter()
    meta=read(folder/'receipt.json')
    h=hashlib.sha256()
    with source.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    probe=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(source)],capture_output=True,text=True,check=True)
    import json
    info=json.loads(probe.stdout);save(folder/'ffprobe.json',info)
    decode=subprocess.run(['ffmpeg','-v','error','-i',str(source),'-map','0:a:0','-ac','1','-ar','16000','-y',str(folder/'audio.wav')],capture_output=True,text=True)
    duration=float(info['format']['duration'])
    row=dict(source_id=sid,url=meta['url'],sha256=h.hexdigest(),bytes=source.stat().st_size,duration_seconds=duration,primary_duration_eligible=duration>=1800,integrity_decode_ok=decode.returncode==0 and not decode.stderr.strip(),decode_stderr=decode.stderr,integrity_scope='full audio decode; audio-only container, no video frames acquired',wall_seconds=time.perf_counter()-start,paid_USD=0)
    save(dest,row);print(sid,duration,row['integrity_decode_ok'])
