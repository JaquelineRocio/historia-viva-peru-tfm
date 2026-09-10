"""Timestamp-preserving pilot units; sentence/discourse review precedes labeling.

Reuses production temporal grouping as anchors, with zero overlap. Cues remain
indivisible and overlength units are flagged, never sliced to fit tokens.
"""
import hashlib
import json
import re
import sys
from collections import Counter

from prepare_beto_v3 import ART, OUT, ROOT, read, sha, write

sys.path.insert(0,str(ROOT/'apps/ml'))
from app.segmentation import segment_by_time

def main():
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
    units=[]
    sources=[]
    acquisition=OUT/'acquisition'
    for receipt in sorted(acquisition.glob('*/receipt.json')):
        meta=read(receipt)
        sid=meta['video_id']
        source={**meta,'receipt_sha256':sha(receipt)}
        if meta['role']=='S':
            source['units_generated']=0
            sources.append(source)
            continue
        cues=read(receipt.parent/'cues.json')
        assert sha(receipt.parent/'cues.json')==meta['captions_sha256']
        # These anchors are NOT accepted discourse units until reviewed.
        anchors=segment_by_time(cues,window_sec=75,overlap_sec=0)
        for i,anchor in enumerate(anchors):
            selected=[(j,c) for j,c in enumerate(cues) if int(c['start']//75)==int(anchor.start_sec//75)]
            original=' '.join(c['text'].strip() for _,c in selected if c['text'].strip())
            normalized=re.sub(r'\s+',' ',original).strip()
            tokens=tok(normalized,add_special_tokens=True,truncation=False)['input_ids']
            flags=['discourse_boundary_review_required']
            if len(tokens)>384:
                flags.append('would_truncate')
            units.append({'segment_id':f'{sid}-u{i+1:03}','source_id':sid,'family_id':meta['family_id'],
                'v3_role':meta['role'],'start_sec':anchor.start_sec,'end_sec':anchor.end_sec,
                'cue_indices':[j for j,_ in selected],'text_original':original,'text':normalized,
                'text_sha256':hashlib.sha256(normalized.encode()).hexdigest(),
                'source_sha256':meta['captions_sha256'],'tokens_with_specials':len(tokens),
                'truncated_tokens_if_used':max(0,len(tokens)-384),'label':None,
                'reference_status':'unannotated','quality_flags':flags,
                'normalization':'whitespace_only','segmentation':'production segment_by_time(75,0); review required',
                'training_eligible':False})
        source['units_generated']=len(anchors)
        source['coverage_method']='all returned cues; beginning/end and gaps listed in receipt; no audio verification'
        sources.append(source)
    for fail in sorted(acquisition.glob('*/failure-*.json')):
        failure=read(fail)
        if failure['video_id'] not in {s['video_id'] for s in sources}:
            sources.append({**failure,'status':'blocked','units_generated':0,'receipt_sha256':sha(fail)})
    write(OUT/'video-unit-candidates.json',{'version':'pilot-units-01','items':units})
    write(ART/'source-registry.json',{'sources':sources,
        'inherited_reservations':read(ART/'reserved-index.json'),
        'family_rule':'original work, not channel; all reproductions inherit assigned role',
        'alias_groups':[{'family_id':'video-KIZbI_9WDQA','video_ids':['KIZbI_9WDQA','8C8yyQtbZ3E'],'role':'T'}],
        'independence_check_status':'video IDs absent from historical source IDs; cross-work excerpts still require review'})
    for role in ['T','V']:
        selected=[u for u in units if u['v3_role']==role]
        write(OUT/f'annotation/{role}-input.json',{'guide_sha256':sha(ROOT/'docs/beto-v3/guia-etiquetado-v3.md'),
            'model':'GPT-6 (Codex system identity); exact backend weights unknown',
            'configuration':{'temperature':'unknown','seed':'unknown'},
            'items':selected,'acceptance':'Resolve discourse boundaries before accepted labels; text changes invalidate annotations'})
    counts=dict(Counter(u['v3_role'] for u in units))
    result={'transcripts_obtained':sum(s.get('cues',0)>0 for s in sources),
        'long_transcripts_30min':sum(s.get('cues',0)>0 and s.get('duration_seconds',0)>=1800 for s in sources),
        'candidate_units':counts,'accepted_references':0,'overlength_units':sum(u['tokens_with_specials']>384 for u in units),
        'role_works':{role:len({u['source_id'] for u in units if u['v3_role']==role}) for role in ['T','V']},
        'status':'pilot_only; C gate closed','blockers':['Cádiz and Sánchez Carrión lack public captions',
            'Cádiz audio acquisition HTTP 403; no ASR audio available',
            'Only one validation video acquired; seven-class references not yet established',
            'Discourse boundaries and annotation review pending'],
        'S_text_accessed':False,'new_training_runs':0,'new_training_gpu_seconds':0,'ASR_gpu_seconds':0}
    write(ART/'phase-B-summary.json',result)
    print(json.dumps(result))

if __name__=='__main__':
    main()
