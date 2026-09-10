"""At most eight gap-driven candidates; public captions only, no paid service.

Sequential attempts, no bypasses or repeated blocked downloads. New material
is kept outside the completed 123-candidate annotation batch.
"""
import html
import json
import re
import time
from datetime import datetime, timezone

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from prepare_beto_v3 import ROOT, OUT, ART, read, sha, write

SOURCES=[
 ('N01','V','TVPerú','Reformas Borbónicas (14/03/2016)',
  'https://www.youtube.com/watch?v=KHcAIKD38sI','contexto_colonial_antecedentes','KHcAIKD38sI',None),
 ('N02','V','TVPerú','Batalla de Ayacucho (14/12/2024)',
  'https://www.tvperu.gob.pe/videos/sucedio-en-el-peru/sucedio-en-el-peru-batalla-de-ayacucho-14122024-tvperu','campanias_conflictos_militares',None,'HTTP 403 from web reader in this task; no alternate retrieval of blocked page'),
 ('N03','V','PUCP / Instituto Riva-Agüero','Francisco de Zela',
  'https://videos.pucp.edu.pe/videos/ver/1e45d7298d0bb0ef1abfa440eb322b6c','crisis_ideas_emancipadoras;liderazgos_diplomacia_proyectos',None,None),
 ('N04','V','PUCP / Argos','Consolidación de la Independencia del Perú',
  'https://estudios-generales-letras.pucp.edu.pe/vuelve-a-ver-el-documental-consolidacion-de-la-independencia-del-peru/','campanias_conflictos_militares',None,None),
 ('N05','T','IRTP / TVPerú','La mujer peruana en la independencia',
  'https://www.irtpplay.gob.pe/episodios/sucedio-en-el-peru/la-mujer-peruana-en-la-independencia','participacion_social_regional',None,None),
 ('N06','T','IEP','La independencia y la cultura política peruana (1808-1821)',
  'https://iep.org.pe/actividades/presentacion-del-libro-la-independencia-y-la-cultura-politica-peruana-1808-1821-de-victor-peralta-ruiz/','crisis_ideas_emancipadoras',None,None),
 ('N07','V','PUCP','Simposio: La iglesia ante el desafío de la independencia del Perú',
  'https://educast.pucp.edu.pe/video/12047/simposio_la_iglesia_ante_el_desafio_de_la_independencia_del_peru','contexto_colonial_antecedentes;participacion_social_regional',None,None),
 ('N08','T','PUCP','De Cádiz a Aznapuquio: militares españoles, 1813-1821',
  'https://educast.pucp.edu.pe/video/2647/xxii_coloquio_internacional_de_estudiantes_de_historia_mesa_12_la_independencia_hispanoamericana_las_diversas_trayectorias_de_sus_personajes2_de_4','crisis_ideas_emancipadoras;campanias_conflictos_militares',None,None),
]

def main():
    dest=OUT/'phase-b-completion-01/new-sources'
    manifest=[dict(zip(['source_id','proposed_role','institution','title','url','gap','video_id','known_block'],r)) for r in SOURCES]
    write(ART/'phase-b-completion-01/source-acquisition-plan.json',{'sources':manifest,'max_candidates':8,
        'based_on_sha256':sha(ART/'phase-b-completion-01/coverage-by-class-work-partition.csv'),
        'selection_basis':'V has zero colonial/military proposals and only one work; T has one colonial proposal and fewer than 20/class',
        'roles_fixed_before_content':True,'content_labels_not_inferred_from_topic':True})
    old_registry=read(ART/'source-registry.json')
    existing={s.get('video_id'):s.get('role') for s in old_registry['sources'] if s.get('video_id')}
    # Only reservation metadata is accessed, never its captions/labels.
    for p in (ROOT/'outputs/beto-v2/corpus').glob('V*/acquisition.json'):
        acquisition=read(p)
        if p.parent.name in {'V03','V04'}:
            for vid in acquisition.get('video_ids',[]):existing[vid]='S'
    results=[]
    for source in manifest:
        folder=dest/source['source_id'];receipt=folder/'receipt.json'
        if receipt.exists():
            results.append(read(receipt));print(source['source_id'],'cached',flush=True);continue
        folder.mkdir(parents=True,exist_ok=True)
        started=time.perf_counter()
        record={**source,'acquired_at':datetime.now(timezone.utc).isoformat(),
            'status':'metadata_candidate','speaker':None,'duration_seconds':None,
            'family_id':'candidate-'+source['source_id'],'independence_status':'pending_original_work_and_excerpt_comparison',
            'training_eligible':False,'caption_units_annotated':0}
        try:
            if source['known_block']:raise ValueError(source['known_block'])
            session=requests.Session();original=session.request
            session.request=lambda *a,**kw:original(*a,**dict({'timeout':20},**kw))
            vid=source['video_id']
            if not vid:
                response=session.get(source['url']);response.raise_for_status()
                page=html.unescape(response.text)
                write(folder/'landing.html',response.content)
                record['landing_sha256']=sha(folder/'landing.html')
                ids=list(dict.fromkeys(re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([\w-]{11})',page)))
                record['linked_video_ids']=ids
                record['linked_media']=list(dict.fromkeys(re.findall(r'https?[^\s"<>]+\.(?:vtt|srt|mp4|mp3)(?:\?[^\s"<>]*)?',page)))[:20]
                if len(ids)!=1:
                    raise ValueError('No unique directly linked YouTube video; preserve media links for source review')
                vid=ids[0];record['video_id']=vid
            if vid in existing:
                record['existing_role']=existing[vid]
                raise ValueError('Existing/reserved video: inherit role; no duplicate acquisition across partitions')
            existing[vid]=source['proposed_role']
            record['family_id']='video-'+vid
            response=session.get('https://www.youtube.com/watch?v='+vid);response.raise_for_status()
            match=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',response.text)
            if match:
                player,_=json.JSONDecoder().raw_decode(response.text[match.end():])
                details=player.get('videoDetails',{})
                record.update(title=details.get('title',record['title']),channel=details.get('author'),
                    channel_id=details.get('channelId'),duration_seconds=int(details['lengthSeconds']) if details.get('lengthSeconds') else None)
            transcripts=YouTubeTranscriptApi(http_client=session).list(vid)
            try:transcript=transcripts.find_manually_created_transcript(['es','es-ES','es-419'])
            except Exception:transcript=transcripts.find_generated_transcript(['es','es-ES','es-419'])
            cues=transcript.fetch().to_raw_data()
            write(folder/'cues.json',cues)
            ends=[c['start']+c['duration'] for c in cues]
            record.update(status='captions_obtained_pending_QA',captions_sha256=sha(folder/'cues.json'),
                cues=len(cues),transcription_method='public_youtube_captions',is_generated=transcript.is_generated,
                caption_start=min(c['start'] for c in cues),caption_end=max(ends),
                gaps_over_15_seconds=[{'after_cue':i-1,'seconds':cues[i]['start']-ends[i-1]} for i in range(1,len(cues)) if cues[i]['start']-ends[i-1]>15])
        except Exception as error:
            record.update(status='blocked_or_needs_source_review',error_type=type(error).__name__,error=str(error),
                user_file_if_available='Complete original Spanish SRT/VTT with timestamps, or original audio/video plus verified duration; do not provide summaries',
                file_purpose=source['gap'])
        record['seconds']=time.perf_counter()-started
        write(receipt,record);results.append(record)
        print(source['source_id'],record['status'],record.get('video_id'),flush=True)
    write(ART/'phase-b-completion-01/source-registry-updated.json',{'parent_sha256':sha(ART/'source-registry.json'),
        'existing_sources':old_registry['sources'],'inherited_reservations':old_registry['inherited_reservations'],
        'existing_alias_groups':old_registry['alias_groups'],'new_candidates':results,
        'S_closed':True,'services_paid_USD':0,'new_candidate_count':len(results),
        'important':'New acquisitions are pending original-work duplicate/excerpt and integrity review, not accepted V or T data'})

if __name__=='__main__':
    main()
