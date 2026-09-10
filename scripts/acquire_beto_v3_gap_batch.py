"""Acquire public captions with fixed roles, cached receipts and no paid services."""
import argparse, hashlib, json, re, time
from datetime import datetime, timezone
from pathlib import Path
import requests
from youtube_transcript_api import YouTubeTranscriptApi

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'outputs/beto-v3/phase-b-gap-02'
ART = ROOT / 'artifacts/beto-v3/phase-b-gap-02'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    tmp.replace(p)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--retry-blocked', action='store_true')
    args=parser.parse_args()
    plan=read(ART/'acquisition-plan.json')
    registry=read(ROOT/'artifacts/beto-v3/phase-b-completion-01/source-registry-final.json')
    existing={r.get('video_id'):r.get('role',r.get('proposed_role')) for r in registry['existing_sources']+registry['new_candidates'] if r.get('video_id')}
    for reserved in plan.get('reserved_sources',[]):
        assert existing.get(reserved['video_id'],'S')=='S'
        existing[reserved['video_id']]='S'
    for group in registry['existing_alias_groups']:
        for vid in group['video_ids']: existing[vid]=group['role']
    for sid in ['V03','V04']:
        for vid in read(ROOT/f'outputs/beto-v2/corpus/{sid}/acquisition.json').get('video_ids',[]): existing[vid]='S'
    for source in plan['sources']:
        folder=DEST/source['source_id']; receipt=folder/'receipt.json'
        if receipt.exists() and (not args.retry_blocked or read(receipt)['status']=='captions_obtained_pending_QA'): continue
        vid=source['video_id']
        assert existing.get(vid,source['role'])==source['role'] and source['role']!='S'
        existing[vid]=source['role']
        row={**source,'acquired_at':datetime.now(timezone.utc).isoformat(),'services_paid_USD':0,'training_eligible':False,'independence_status':'pending_metadata_and_content_comparison','duration_seconds':None}
        start=time.perf_counter()
        try:
            session=requests.Session(); original=session.request
            session.request=lambda *a,**kw:original(*a,**dict({'timeout':20},**kw))
            response=session.get(source['url']);response.raise_for_status()
            match=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',response.text)
            if not match: raise ValueError('No player metadata')
            player,_=json.JSONDecoder().raw_decode(response.text[match.end():])
            details=player.get('videoDetails',{})
            save(folder/'video-details.json',details)
            row.update(title=details.get('title',source['title']),channel=details.get('author'),duration_seconds=int(details.get('lengthSeconds',0)),family_id='video-'+vid)
            if row['duration_seconds']<1800: raise ValueError('Below 30 minutes; no primary acquisition')
            transcripts=YouTubeTranscriptApi(http_client=session).list(vid)
            try: transcript=transcripts.find_manually_created_transcript(['es','es-ES','es-419'])
            except Exception: transcript=transcripts.find_generated_transcript(['es','es-ES','es-419'])
            cues=transcript.fetch().to_raw_data();save(folder/'cues.json',cues)
            row.update(status='captions_obtained_pending_QA',transcription_method='public_youtube_captions',is_generated=transcript.is_generated,cues=len(cues),captions_sha256=hashlib.sha256((folder/'cues.json').read_bytes()).hexdigest(),caption_start=min(c['start'] for c in cues),caption_end=max(c['start']+c['duration'] for c in cues))
        except Exception as e: row.update(status='blocked_or_needs_source_review',error_type=type(e).__name__,error=str(e))
        row['wall_seconds']=time.perf_counter()-start;save(receipt,row)
        print(source['source_id'],row['status'],row['duration_seconds'],row.get('error_type'),flush=True)
    save(ART/'acquisition-summary.json',{'items':[read(p) for p in sorted(DEST.glob('*/receipt.json'))],'S_closed':True,'services_paid_USD':0})

if __name__=='__main__': main()
