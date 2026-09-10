"""Acquire public video metadata/captions once; keep receipts and failed attempts.

No cookies, proxies, paid API, automatic retries or reserved text acquisition.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from youtube_transcript_api import YouTubeTranscriptApi

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/beto-v3/acquisition'
SOURCES = [
    ('HuT0aI_mDqM', 'T', 'IEP', 'Entrevista Carlos Contreras', 'V01'),
    ('lrV0mu1iZCI', 'T', 'IEP', 'Rolando Rojas: congreso bicentenario', 'V02'),
    ('0Dgk3uh0ziE', 'T', 'IEP', 'La república imaginada: presentación de libro', None),
    ('rKbC4guGhRY', 'V', 'TVPerú', 'Visiones de la independencia (18/07/2021)', None),
    ('bVrm2pJw4SA', 'T', 'TVPerú', 'Expedición libertadora (09/05/2021)', None),
    ('-kN3yjl4u1A', 'T', 'TVPerú', 'El pueblo y su independencia (27/07/2015)', None),
]
EXTRA_SOURCES = [
    ('KIZbI_9WDQA', 'T', 'PUCP', 'El Perú y las Cortes de Cádiz', None),
    ('-Ma1tt97eFg', 'V', 'TVPerú', 'José Faustino Sánchez Carrión (01/06/2015)', None),
    ('zb5zntF2kAs', 'S', 'TVPerú', 'Hipólito Unanue (01/02/2016)', None),
]

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert json.loads(path.read_text(encoding='utf-8')) == data, str(path)
    else:
        with path.open('x', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', nargs='*')
    ap.add_argument('--retry', action='store_true', help='Explicit new access attempt; preserves failures')
    args = ap.parse_args()
    # Roles fixed before captions or predictions. Work reproduction checks still required.
    save(OUT / 'candidate-roles.json', {'sources': [dict(video_id=v, role=r, institution=i,
        title=t, inherited_source_id=s, family_id='video-'+v,
        independence='pending_work_and_content_check') for v,r,i,t,s in SOURCES],
        'selection': 'Institutional links and topics; no model predictions',
        'S': 'Existing V03/V04 remain reserved; no reserve text read'})
    save(OUT / 'candidate-roles-02.json', {'sources':[dict(video_id=v,role=r,institution=i,title=t,
        inherited_source_id=s,family_id='video-'+v,independence='pending_work_and_content_check')
        for v,r,i,t,s in EXTRA_SOURCES], 'selection':'Additional topic coverage before annotation or model predictions',
        'reproductions':{'KIZbI_9WDQA':['8C8yyQtbZ3E']}})
    for vid, role, institution, title, old in SOURCES + EXTRA_SOURCES:
        if args.ids and vid not in args.ids:
            continue
        folder = OUT / vid
        if (folder / 'receipt.json').exists():
            print(vid, 'cached', flush=True)
            continue
        if list(folder.glob('failure-*.json')) and not args.retry:
            print(vid, 'previous failure; explicit --retry required', flush=True)
            continue
        folder.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        record = dict(video_id=vid, role=role, institution=institution, title=title,
            family_id='video-'+vid, url='https://www.youtube.com/watch?v='+vid,
            acquired_at=datetime.now(timezone.utc).isoformat(), speaker=None,
            duration_seconds=None, transcription_method=None)
        try:
            session = requests.Session()
            # The library also uses this bounded timeout.
            original_request = session.request
            session.request = lambda *a, **kw: original_request(*a, **dict({'timeout': 25}, **kw))
            response = session.get(record['url'])
            response.raise_for_status()
            page = response.text
            match = re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*', page)
            if not match:
                raise ValueError('Public player metadata unavailable')
            player, _ = json.JSONDecoder().raw_decode(page[match.end():])
            details = player.get('videoDetails', {})
            record.update(title=details.get('title', title), channel=details.get('author'),
                channel_id=details.get('channelId'), duration_seconds=int(details['lengthSeconds']) if details.get('lengthSeconds') else None,
                playability=player.get('playabilityStatus', {}).get('status'))
            if (folder / 'metadata.json').exists():
                record['prior_metadata_sha256']=sha(folder/'metadata.json')
            else:
                save(folder / 'metadata.json', record)
            if role == 'S':
                record.update(status='reserved_metadata_only', seconds=time.perf_counter()-started)
                save(folder / 'receipt.json', record)
                print(vid, 'S: metadata only', record['duration_seconds'], flush=True)
                continue
            if old:
                cues_path = ROOT / f'outputs/beto-v2/corpus/{old}/cues.json'
                cues = json.loads(cues_path.read_text(encoding='utf-8'))
                record.update(transcription_method='inherited_public_captions', inherited_path=str(cues_path.relative_to(ROOT)), inherited_sha256=sha(cues_path))
            else:
                transcripts = YouTubeTranscriptApi(http_client=session).list(vid)
                try:
                    transcript = transcripts.find_manually_created_transcript(['es', 'es-ES', 'es-419'])
                except Exception:
                    transcript = transcripts.find_generated_transcript(['es', 'es-ES', 'es-419'])
                cues = transcript.fetch().to_raw_data()
                record.update(transcription_method='youtube_public_captions', is_generated=transcript.is_generated,
                    language=transcript.language_code)
            save(folder / 'cues.json', cues)
            ends = [c['start'] + c['duration'] for c in cues]
            record.update(cues=len(cues), captions_sha256=sha(folder/'cues.json'),
                caption_start=min(c['start'] for c in cues), caption_end=max(ends),
                gaps_over_15_seconds=[{'after_cue':i-1, 'seconds':cues[i]['start']-ends[i-1]} for i in range(1,len(cues)) if cues[i]['start']-ends[i-1]>15],
                completeness='pending_beginning_end_and_gap_review', seconds=time.perf_counter()-started)
            save(folder / 'receipt.json', record)
            print(vid, record['duration_seconds'], len(cues), flush=True)
        except Exception as exc:
            record.update(error_type=type(exc).__name__, error=str(exc), seconds=time.perf_counter()-started)
            save(folder / ('failure-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'), record)
            print(vid, record['error_type'], str(exc)[:160], flush=True)

if __name__ == '__main__':
    main()
