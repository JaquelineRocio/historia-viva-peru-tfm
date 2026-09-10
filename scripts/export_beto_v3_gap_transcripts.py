"""Export existing authentic captions/ASR to SRT; no transcription or annotation calls."""
from acquire_beto_v3_gap_batch import DEST,ART,read,save
import hashlib
def stamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'
rows=[]
for folder in sorted(DEST.glob('G*')):
    path=folder/'cues.json'
    if not path.exists():path=folder/'asr/cues.json'
    if not path.exists():continue
    cues=read(path);receipt=read(folder/'receipt.json');duration=receipt['duration_seconds']
    text='\n\n'.join(f"{i}\n{stamp(c['start'])} --> {stamp(c.get('end',c['start']+c.get('duration',0)))}\n{c['text']}" for i,c in enumerate(cues,1))+'\n'
    dest=folder/'transcript.srt';dest.write_text(text,encoding='utf-8')
    ends=[c.get('end',c['start']+c.get('duration',0)) for c in cues]
    row=dict(source_id=folder.name,role=receipt['role'],duration_seconds=duration,cues=len(cues),first_cue_seconds=min(c['start'] for c in cues),last_cue_end_seconds=max(ends),leading_interval_without_captions=max(0,min(c['start'] for c in cues)),trailing_interval_without_captions=max(0,duration-max(ends)),max_overrun_seconds=max(0,max(ends)-duration),gaps_over_15_seconds=[dict(start=ends[i-1],end=c['start']) for i,c in enumerate(cues) if i and c['start']-ends[i-1]>15],source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),srt_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),text_modified=False,literal_fidelity_certified=False,coverage_statement='All returned cues retained. Full audio processed only for G03/G17. Uncaptioned intervals not certified silent.')
    save(folder/'transcript-quality.json',row);rows.append(row)
save(ART/'transcript-export.json',{'sources':rows,'S_content_accessed':False,'paid_USD':0})
print(len(rows),'SRT exports, authentic timings retained')
