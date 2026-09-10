"""Verify reserve metadata only. Never list/fetch captions, audio or predictions."""
import json,re,requests
from datetime import datetime,timezone
from acquire_beto_v3_gap_batch import ROOT, ART, read, save
plan=read(ART/'acquisition-plan.json')
dev={r['video_id'] for r in plan['sources']}
old=read(ROOT/'artifacts/beto-v3/source-registry.json')
dev|={r['video_id'] for r in old['sources'] if r['role']!='S'}
dest=ART/'reserve-metadata.json'
rows=read(dest)['sources'] if dest.exists() else []
for source in plan.get('reserved_sources',[]):
    assert source['video_id'] not in dev and source['role']=='S'
    if any(r['video_id']==source['video_id'] for r in rows):continue
    r=requests.get(source['url'],timeout=20);r.raise_for_status()
    match=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',r.text)
    player,_=json.JSONDecoder().raw_decode(r.text[match.end():])
    details=player['videoDetails']
    row={**source,'title':details['title'],'duration_seconds':int(details['lengthSeconds']),'channel':details['author'],'channel_id':details['channelId'],'acquired_at':datetime.now(timezone.utc).isoformat(),'status':'reserved_metadata_only','text_accessed':False,'primary_duration_eligible':int(details['lengthSeconds'])>=1800,'independence_status':'metadata_only_pending_final_relation_admission'}
    rows.append(row);save(dest,{'sources':rows,'S_closed':True,'content_accessed':False,'paid_USD':0});print(source['source_id'],row['duration_seconds'])
