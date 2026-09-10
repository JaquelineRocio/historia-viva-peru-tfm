"""Verify directly exposed institutional media for the same eight candidates."""
from datetime import datetime, timezone
import requests
from prepare_beto_v3 import ART, OUT, read, write, sha

def main():
    root=ART/'phase-b-completion-01'
    registry=read(root/'source-registry-updated.json')
    urls={
        'N03':'https://videos.pucp.edu.pe/new/e/ebb96fcba79873.mp4',
        'N07':'https://educast.pucp.edu.pe/files/videos/f/fe3f4736e14db21/a7bb70c4b9.mp4',
        'N08':'https://educast.pucp.edu.pe/files/videos/2/2f545225e23b935f346b38b3f/56mo444de314795.mp4'}
    for source in registry['new_candidates']:
        if source['source_id'] not in urls:continue
        receipt=OUT/'phase-b-completion-01/new-sources'/source['source_id']/'media-probe.json'
        if receipt.exists():
            probe=read(receipt)
        else:
            url=urls[source['source_id']]
            probe={'url':url,'at_utc':datetime.now(timezone.utc).isoformat(),'method':'HEAD, redirects allowed; no full download'}
            try:
                response=requests.head(url,timeout=20,allow_redirects=True)
                probe.update(status_code=response.status_code,resolved_url=response.url,
                    content_type=response.headers.get('Content-Type'),content_length=response.headers.get('Content-Length'),
                    accessible=response.status_code==200 and 'video' in response.headers.get('Content-Type',''))
            except Exception as error:
                probe.update(accessible=False,error_type=type(error).__name__,error=str(error))
            write(receipt,probe)
        source['direct_media_probe']=probe
        if probe['accessible']:
            source['status']='public_video_accessible_transcription_pending'
            source['user_file_if_available']=None
            source['next_action']='Download public original; run timed local ASR pilot before a full transcription, within separate plan budget'
        if source['source_id']=='N03':
            source['duration_seconds']=1080
            source['duration_provenance']='Institutional landing page: Duración 18:00, not last subtitle'
        print(source['source_id'],probe.get('status_code'),probe['accessible'],flush=True)
    write(root/'source-registry-final.json',{**registry,'parent_update_sha256':sha(root/'source-registry-updated.json'),
        'source_limit_used':8,'notes':'Only the same three publicly exposed media URLs checked; no extra candidate or blocked-page bypass'})

if __name__=='__main__':main()
