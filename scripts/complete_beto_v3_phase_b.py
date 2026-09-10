"""Reproducible full phase-B first pass and honest pending-review export.

Run with the existing ML venv. No network, BETO inference or paid API is used.
Old immutable pilot artifacts remain untouched. The decisions are explicit
assistant reading judgments in beto_v3_phase_b_decisions.py.
"""
import csv
import hashlib
import io
import json
import math
import random
from collections import Counter, defaultdict

from prepare_beto_v3 import ROOT, OUT, ART, read, sha, write
from beto_v3_phase_b_decisions import LONG, SHORT, LABELS, RULES

DEST=OUT/'phase-b-completion-01'
META=ART/'phase-b-completion-01'

def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def csv_write(path, rows, fields):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    write(path,stream.getvalue().encode('utf-8-sig'))

def run():
    if (META/'resume-verification.json').exists():
        print('Reviewed successor exists; preserving first-pass snapshot and saved reviews. Run finalize_beto_v3_resume.py.')
        return
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
    guide_hash=sha(ROOT/'docs/beto-v3/guia-etiquetado-v3.md')
    old=read(OUT/'video-unit-candidates.json')['items']
    previous=read(OUT/'annotation/pilot-first-pass.json')['items']
    reusable={(r['input_sha256'],r['guide_sha256']):r for r in previous}
    all_units=[]
    changes=[]
    problems=[]
    for vid,table in (LONG|SHORT).items():
        original_candidates=[r for r in old if r['source_id']==vid]
        cues_path=OUT/'acquisition'/vid/'cues.json'
        cues=read(cues_path)
        source=' '.join(c['text'].strip() for c in cues)
        cue_spans=[]
        cursor=0
        for i,cue in enumerate(cues):
            text=cue['text'].strip()
            cue_spans.append((cursor,cursor+len(text),i))
            cursor+=len(text)+1
        old_spans=[]
        cursor=0
        for item in original_candidates:
            a=source.index(item['text_original'],cursor)
            z=a+len(item['text_original'])
            old_spans.append((a,z,item['segment_id']))
            cursor=z
        entries=[]
        for line in table.strip().splitlines():
            number,anchor,label,alternative,flags,evidence,reason=line.split('|')
            number=int(number)
            if anchor=='^':
                start=0
            else:
                positions=[]
                at=source.find(anchor)
                while at>=0:
                    positions.append(at)
                    at=source.find(anchor,at+1)
                if not positions:
                    problems.append((vid,number,'missing_anchor',anchor))
                    continue
                expected=old_spans[min(number-1,len(old_spans)-1)][0] if vid in LONG else (entries[-1]['start']+1)
                allowed=[p for p in positions if not entries or p>entries[-1]['start']]
                if not allowed:
                    problems.append((vid,number,'nonmonotone_anchor',anchor))
                    continue
                start=min(allowed,key=lambda p:abs(p-expected))
            entries.append(dict(number=number,start=start,anchor=anchor,code=label,alternative=alternative,
                flags=flags,evidence=evidence,reason=reason))
        if problems:
            continue
        for idx,entry in enumerate(entries):
            a=entry['start']
            z=entries[idx+1]['start'] if idx+1<len(entries) else len(source)
            text=source[a:z].strip()
            if entry['evidence'] not in text:
                problems.append((vid,entry['number'],'missing_evidence',entry['evidence'],text[:100]))
                continue
            parents=[sid for left,right,sid in old_spans if left<z and right>a]
            pieces=[{'cue_index':ci,'cue_char_start':max(a,left)-left,'cue_char_end':min(z,right)-left}
                for left,right,ci in cue_spans if left<z and right>a and right>left]
            tokens=tok(text,truncation=False,add_special_tokens=True)['input_ids']
            cached=reusable.get((digest(text),guide_hash))
            label=LABELS[entry['code']]
            alternative=LABELS.get(entry['alternative'])
            ambiguous='A' in entry['flags']
            extraction='E' in entry['flags']
            evidence=entry['evidence']
            reason=entry['reason']
            if cached:
                label=cached['proposal'];alternative=cached['alternative'];ambiguous=cached['ambiguous']
                extraction=cached['extraction_defect'];evidence=cached['evidence'];reason=cached['reason']
            unit={'segment_id':f'{vid}-b01-{entry["number"]:03}','source_id':vid,'family_id':'video-'+vid,
                'partition':original_candidates[0]['v3_role'],'text_original':source[a:z], 'text':text,
                'input_sha256':digest(text),'source_sha256':sha(cues_path),'source_char_span':[a,z],
                'cue_pieces':pieces,'parent_candidate_ids':parents,
                'start_sec':min(cues[p['cue_index']]['start'] for p in pieces),
                'end_sec':max(cues[p['cue_index']]['start']+cues[p['cue_index']]['duration'] for p in pieces),
                'timestamp_precision':'original subtitle cue; partial-cue cut has no invented word timestamp',
                'tokens_with_specials':len(tokens),'would_truncate_tokens':max(0,len(tokens)-384),
                'proposal':label,'alternative':alternative,'rule':RULES[entry['code']],
                'evidence':evidence,'evidence_span':[text.index(evidence),text.index(evidence)+len(evidence)],
                'rationale':reason,'ambiguous':ambiguous,'extraction_defect':extraction,
                'segmentation_review':'manual transcript reading; exact discourse anchor',
                'boundary_pending':extraction,'input_representation':'authentic_target_only_whitespace_trim',
                'guide_sha256':guide_hash,'first_pass_origin':'reused_exact_text_and_guide' if cached else 'current_Codex_reading',
                'reused_annotation_id':cached['segment_id'] if cached else None,
                'model':'GPT-6 Codex (system identity); exact backend weights unknown',
                'configuration':{'temperature':'unknown','seed':'unknown'},'second_review':None,
                'expert_reference':False,'training_eligible':False}
            all_units.append(unit)
            changes.append({'unit_id':unit['segment_id'],'parents':parents,'source_char_span':[a,z],
                'start_anchor':entry['anchor'],'cue_pieces':pieces,
                'operation':'resegment_contiguous_authentic_text; preserve all source characters',
                'joins_parent_candidates':len(parents)>1,
                'ends_at_next_discourse_anchor':idx+1<len(entries),'text_rewritten':False})
    if problems:
        print(json.dumps(problems,ensure_ascii=False,indent=2))
        raise SystemExit(1)
    over=[(r['segment_id'],r['tokens_with_specials']) for r in all_units if r['would_truncate_tokens']]
    if over:
        print('OVERLENGTH',over)
        raise SystemExit(1)
    assert {p for r in all_units for p in r['parent_candidate_ids']}=={r['segment_id'] for r in old}
    # Fixed PRNG over sorted eligible T IDs. No class/prediction-based selection.
    train_clear=sorted([r['segment_id'] for r in all_units if r['partition']=='T' and not r['ambiguous'] and not r['extraction_defect']])
    n=math.ceil(.20*len(train_clear))
    sampled=set(random.Random(20260909).sample(train_clear,n))
    review=[]
    for row in all_units:
        reasons=[]
        if row['partition']=='V':reasons.append('all_validation')
        if row['ambiguous']:reasons.append('ambiguous_training' if row['partition']=='T' else 'ambiguous_validation')
        if row['segment_id'] in sampled:reasons.append('random_20_percent_training')
        if row['extraction_defect']:reasons.append('source_or_boundary_check')
        row['review_reasons']=reasons
        row['status']='pending_review' if reasons else 'accepted_first_pass_unsampled_training'
        row['accepted_label']=None if reasons else row['proposal']
        if reasons:
            # Review input excludes proposals, alternatives and rationales.
            review.append({k:row[k] for k in ['segment_id','source_id','family_id','partition','text','input_sha256',
                'source_sha256','cue_pieces','start_sec','end_sec','guide_sha256']})
    coverage=[]
    for partition in ['T','V']:
        for source in sorted({r['source_id'] for r in all_units if r['partition']==partition}):
            for label in LABELS.values():
                rows=[r for r in all_units if r['partition']==partition and r['source_id']==source and r['proposal']==label]
                coverage.append({'partition':partition,'work':source,'class':label,'proposed':len(rows),
                    'accepted':sum(r['accepted_label'] is not None for r in rows),
                    'pending':sum(r['accepted_label'] is None for r in rows),
                    'ambiguous':sum(r['ambiguous'] for r in rows),'source_or_boundary_pending':sum(r['extraction_defect'] for r in rows)})
    old_input_hashes={r['input_sha256'] for r in previous}
    summary={'version':'phase-b-completion-01','old_candidates_processed':len(old),'result_units':len(all_units),
        'class_proposals':dict(Counter(r['proposal'] for r in all_units)),
        'status_counts':dict(Counter(r['status'] for r in all_units)),
        'reused_first_pass':sum(r['first_pass_origin'].startswith('reused') for r in all_units),
        'new_distinct_annotated_inputs':len({r['input_sha256'] for r in all_units}-old_input_hashes),
        'cumulative_distinct_annotated_inputs':len({r['input_sha256'] for r in all_units}|old_input_hashes),
        'second_review_executed':0,'pending_review_export':len(review),
        'review_capability':'No callable independent text-model completion tool used; no isolated second pass executed. Current reading is a single pass, not blind review.',
        'review_sampling':{'seed':20260909,'eligible_unambiguous_T':len(train_clear),'sample_size':n,'fraction':.20,'ids':sorted(sampled)},
        'accepted_reference_meaning':'Unambiguous training first-pass references outside required 20% sample; not expert gold. All rows remain globally training-ineligible until phase-B gates pass.',
        'services_paid_USD':0,'training_runs':0,'ASR_runs':0,'S_content_opened':False}
    assert summary['cumulative_distinct_annotated_inputs']<=1200
    write(DEST/'units-and-annotations.json',{'items':all_units})
    write(META/'segmentation-changes.json',{'changes':changes,'coverage':'all 123 parent candidates; complete text partition in source order, no dropped content'})
    write(DEST/'review-input-blind.json',{'guide':str((ROOT/'docs/beto-v3/guia-etiquetado-v3.md').relative_to(ROOT)),
        'items':review,'instructions':'Assign a fresh label with evidence and flags using target only. Do not open first-pass decisions. No BETO predictions.'})
    write(META/'summary.json',summary)
    csv_write(META/'coverage-by-class-work-partition.csv',coverage,list(coverage[0]))
    csv_write(DEST/'annotations.csv',[{k:r[k] for k in ['segment_id','partition','source_id','proposal','accepted_label','status','ambiguous','extraction_defect','evidence','rationale']} for r in all_units],
        ['segment_id','partition','source_id','proposal','accepted_label','status','ambiguous','extraction_defect','evidence','rationale'])
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    run()
