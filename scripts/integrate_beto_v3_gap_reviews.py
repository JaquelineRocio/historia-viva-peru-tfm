"""Validate frozen blind responses and explicit adjudications; integrate references only."""
import argparse, csv, hashlib, io, json
from collections import Counter
from acquire_beto_v3_gap_batch import ROOT, DEST, ART, read, save

RUN=DEST/'review-run-01'
META=ART/'review-run-01'
GLOBAL=ROOT/'artifacts/beto-v3'
PARENT=ROOT/'outputs/beto-v3/phase-b-completion-01/all-development-units.json'
PARENT_SHA='344eb020f2fc5b0c34ad1a15f5ce7ec0c48b7d5272220f1f39d65bd5fe44e0eb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvout(p,rows):
    s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    p.write_bytes(s.getvalue().encode('utf-8-sig'))
def exact(u,r,guide):
    assert r['input_sha256']==u['input_sha256']==hashlib.sha256(u['text'].encode()).hexdigest()
    assert r['guide_sha256']==guide
    a,z=r['evidence_span'];assert isinstance(a,int) and isinstance(z,int) and 0<=a<z<=len(u['text'])
    assert u['text'][a:z]==r['evidence']
def collect():
    assert sha(PARENT)==PARENT_SHA,'Inherited references changed'
    labels=set(read(GLOBAL/'protocol.json')['labels'])
    guide=sha(ROOT/'docs/beto-v3/guia-etiquetado-v3.md')
    units={u['segment_id']:u for p in DEST.glob('*/annotation/units.json') for u in read(p)['items']}
    first={u['segment_id']:u for p in DEST.glob('*/annotation/first-pass/batch-*.json') for u in read(p)['items']}
    # This integration is deliberately scoped to the frozen first 251, not later lots.
    frozen_ids=set(read(META/'adjudication-signoff.json')['all_ids'])
    assert len(frozen_ids)==251 and frozen_ids<=first.keys()
    first={k:first[k] for k in frozen_ids}
    blind={};second={};response_files={}
    for n in range(1,16):
        p=RUN/f'batch-{n:03}.json';packet=read(p)
        assert hashlib.sha256(packet['guide'].encode()).hexdigest()==guide
        q=RUN/'second-review'/p.name;response=read(q)
        assert response['blind_context'] is True
        assert {u['segment_id'] for u in packet['items']}=={u['segment_id'] for u in response['items']}
        assert len(packet['items'])==len(response['items'])
        for u in packet['items']:
            assert set(u)=={'segment_id','text','input_sha256','guide_sha256'}
            assert u['text']==units[u['segment_id']]['text'];assert u['segment_id'] not in blind
            blind[u['segment_id']]=u
        for r in response['items']:
            sid=r['segment_id'];assert sid not in second
            exact(units[sid],r,guide);assert r['proposal'] in labels|{None}
            second[sid]=r;response_files[sid]=str(q.relative_to(ROOT))
    queue=read(ART/'blind-review-queue.json')
    assert set(blind)=={sid for group in queue['selection'] for sid in group['selected_ids']}
    assert len(second)==211
    adjud=read(RUN/'adjudications.json')['items'];decisions={r['segment_id']:r for r in adjud}
    assert len(decisions)==len(adjud)==251 and set(decisions)==set(first)
    receipts={r['source_id']:r for p in DEST.glob('*/receipt.json') for r in [read(p)]}
    new=[];comparison=[];cache=[]
    for sid in sorted(first):
        a=first[sid];u=units[sid];d=decisions[sid];b=second.get(sid)
        exact(u,a,guide);exact(u,d,guide)
        assert a['accepted_label'] is None and not a['training_eligible']
        assert d['accepted_label'] in labels|{None} and d['reviewer']=='parent-text-guide-adjudication'
        assert d['boundary_checked'] and d['evidence_checked']
        assert not d['accepted_label'] or not d['boundary_blocking']
        if b is None:
            assert u['partition']=='T' and not a['ambiguous'] and not a['extraction_defect']
            assert d['review_path']=='T_unsampled_first_pass_with_parent_check'
        else:assert d['review_path']=='blind_second_plus_parent_adjudication'
        row=dict(u);row.update({k:v for k,v in a.items() if k not in ['accepted_label','training_eligible']})
        row.update(first_pass=a,second_review=b,adjudication=d,accepted_label=d['accepted_label'],training_eligible=False,
            reference_status='accepted_reference' if d['accepted_label'] else 'pending_resolution',source_admission='pending_final_work_admission')
        row['original_family_id']=u['family_id'];row['family_id']='video-'+receipts[u['source_id']]['video_id']
        new.append(row)
        if b:
            comparison.append(dict(segment_id=sid,first=a['proposal'],second=b['proposal'],label_agreement=a['proposal']==b['proposal'],accepted_label=d['accepted_label'],rationale=d['rationale']))
            key=dict(text_sha256=u['input_sha256'],context=None,guide_sha256=guide,configuration=b['exposed_configuration'],prompt_version=b['prompt_version'],model=b['model'])
            cache.append(dict(segment_id=sid,key=key,cache_key_sha256=hashlib.sha256(json.dumps(key,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),response_file=response_files[sid],response_file_sha256=sha(ROOT/response_files[sid])))
    return read(PARENT)['items'],new,comparison,cache

def main(check_only=False):
    if (ROOT/'artifacts/beto-v3/recovery-01/current.json').exists():
        from integrate_beto_v3_recovery import main as recovery
        return recovery(check_only=check_only)
    if (ART/'selected-444/current.json').exists():
        from integrate_beto_v3_selected444 import main as selected
        return selected(check_only=True)
    old,new,comparison,cache=collect();rows=old+new
    assert len({r['segment_id'] for r in rows})==len(rows)==486
    roles={}
    for r in rows:
        assert r['partition']!='S' and not r['training_eligible']
        roles.setdefault(r['family_id'],set()).add(r['partition'])
    assert all(len(v)==1 for v in roles.values())
    reserved=read(GLOBAL/'reserved-index.json')
    assert sha(ROOT/reserved['inherited_final']['manifest'])==reserved['v2_reserved_manifest_sha256']
    before=read(META/'before/budget-ledger-current.json');ledger=read(GLOBAL/'budget-ledger-current.json')
    assert ledger['new_unique_annotation_proposals']==before['new_unique_annotation_proposals']==494
    assert ledger['annotation_budget_remaining']==706 and ledger['services_paid_USD']==0
    assert ledger['ASR_gpu_seconds']==before['ASR_gpu_seconds'] and ledger['new_training_trajectories']==0
    if check_only:
        report=read(ART/'review-integration.json')
        assert sha(DEST/'all-development-units.json')==report['all_development_units_sha256']
        assert read(DEST/'all-development-units.json')['items']==rows
        for item in report['input_manifest']:assert sha(ROOT/item['path'])==item['sha256']
        assert ledger['phase_B_second_review_units']==before['phase_B_second_review_units']+211
        print(json.dumps(dict(integrity='passed',second_reviews=211,adjudications=251,unchanged_parent_units=235,S_closed=True)))
        return report
    registry=read(GLOBAL/'phase-b-completion-01/source-registry-final.json')
    durations={r.get('video_id',r.get('source_id')):r.get('duration_seconds',0) or 0 for r in registry['existing_sources']}
    durations.update({r['source_id']:r.get('duration_seconds',0) or 0 for r in registry['new_candidates']})
    durations.update({r['source_id']:r['duration_seconds'] for p in DEST.glob('*/receipt.json') for r in [read(p)]})
    labels=read(GLOBAL/'protocol.json')['labels'];gaps=[]
    for role,target in [('T',20),('V',25)]:
        for label in labels:
            accepted=[r for r in rows if r['partition']==role and r['accepted_label']==label and durations.get(r['source_id'],0)>=1800]
            works=len({r['family_id'] for r in accepted})
            gaps.append(dict(partition=role,**{'class':label},accepted_from_30min_works=len(accepted),target=target,missing_examples=max(0,target-len(accepted)),accepted_30min_works=works,missing_works=max(0,2-works)))
    works=[]
    for sid in sorted({r['source_id'] for r in rows}):
        group=[r for r in rows if r['source_id']==sid];n=sum(r['accepted_label'] is not None for r in group)
        works.append(dict(work=sid,partition=group[0]['partition'],duration_seconds=durations.get(sid,0),units=len(group),accepted=n,pending=len(group)-n,resolvable_reference_fraction=n/len(group)))
    accepted=Counter(r['partition'] for r in rows if r['accepted_label']);gains=Counter(r['partition'] for r in new if r['accepted_label'])
    pending=[r for r in rows if not r['accepted_label']]
    blockers=[f"{r['partition']}/{r['class']}: missing {r['missing_examples']} references and {r['missing_works']} works from >=30-minute sources" for r in gaps if r['missing_examples'] or r['missing_works']]
    long_counts={role:sum(r['accepted_from_30min_works'] for r in gaps if r['partition']==role) for role in ['T','V']}
    for role,target in [('T',300),('V',200)]:
        if long_counts[role]<target:blockers.append(f'{role}: {long_counts[role]}/{target} references from >=30-minute works; missing {target-long_counts[role]}')
        total=sum(r['partition']==role for r in rows)
        if accepted[role]/total<.9:blockers.append(f'{role}: unique reference coverage {accepted[role]}/{total} below 0.90')
    blockers+=['Final original-work admission and H/T/V/S manifests not frozen; acquired work counts remain provisional',f'{len(pending)} units lack a unique reference; preserve inventory; resolve with additional evidence where possible','Caption/audio fidelity and missing-cue intervals remain to be reviewed before final source admission']
    report=dict(version='phase-b-gap-02-review-01',passed=True,parent_units=235,parent_sha256=PARENT_SHA,new_first_pass_units=251,blind_second_reviews=211,T_unsampled_parent_checked=40,adjudications=251,
        label_agreements=sum(r['label_agreement'] for r in comparison),label_disagreements=sum(not r['label_agreement'] for r in comparison),accepted_new_references=sum(gains.values()),accepted_new_by_partition=dict(gains),accepted_references=dict(accepted),accepted_30min_references=long_counts,pending_new_references=sum(not r['accepted_label'] for r in new),pending_references=len(pending),C_ready=False,S_content_opened=False,training_runs=0,same_model_family_both_passes=True,model_weights='unknown',blockers=blockers,
        annotation_status_note='AI-assisted reference judgments, not expert gold or admission to training. Three history-free sessions of the same model family; 40 T units not sampled for blind second review.')
    save(DEST/'new-reviewed-units.json',dict(items=new));save(DEST/'all-development-units.json',dict(parent=str(PARENT.relative_to(ROOT)),parent_sha256=PARENT_SHA,items=rows))
    save(DEST/'pending-resolution.json',dict(items=pending,S_closed=True));save(META/'review-comparison.json',dict(items=comparison));save(META/'second-review-cache.json',dict(items=cache))
    csvout(ART/'exact-gaps-30min-works.csv',gaps);csvout(ART/'coverage-by-work.csv',works)
    csvout(DEST/'annotations.csv',[dict(segment_id=r['segment_id'],source_id=r['source_id'],partition=r['partition'],proposal=r.get('proposal'),accepted_label=r.get('accepted_label'),status=r['reference_status']) for r in rows])
    report['all_development_units_sha256']=sha(DEST/'all-development-units.json')
    inputs=list(sorted((RUN/'second-review').glob('batch-*.json')))+list(sorted(RUN.glob('batch-*.json')))+[RUN/'adjudications.json',META/'adjudication-signoff.json',PARENT]
    inputs+=list(sorted(DEST.glob('*/annotation/first-pass/batch-*.json')))
    report['input_manifest']=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in inputs]
    for key,delta in [('phase_B_second_review_units',211),('phase_B_second_review_batches',15),('phase_B_second_review_calls',3)]:
        expected=before[key]+delta;assert ledger[key] in [before[key],expected];ledger[key]=expected
    ledger['gap_02_blind_review_sessions']=3;ledger['gap_02_second_review_units']=211
    ledger['gap_02_second_review_batches']=15;ledger['gap_02_adjudicated_inputs']=251
    ledger['review_call_count_note']='phase_B_second_review_calls counts isolated reviewer sessions; actual provider invocation/token counts unknown'
    save(GLOBAL/'budget-ledger-current.json',ledger)
    save(ART/'review-integration.json',report);save(GLOBAL/'phase-B-summary.json',report)
    save(GLOBAL/'annotation-progress.json',dict(unique_new_units_with_proposal=494,accepted_references=dict(accepted),accepted_for_training=0,second_review_units=ledger['phase_B_second_review_units'],same_model_family=True,pending=len(pending),V_references_frozen=False,S_references_frozen=False,provider_usage_tokens=None,remaining_annotation_ceiling=706,gap_02_second_reviews=211))
    queue=read(ART/'blind-review-queue.json');queue.update(second_reviews_completed=211,adjudications_completed=211,independence='Three history-free same-model sessions; not independent models',responses=str((RUN/'second-review').relative_to(ROOT)));save(ART/'blind-review-queue.json',queue)
    checkpoint=read(ART/'checkpoint.json');checkpoint.update(accepted_new_references=sum(gains.values()),second_reviews_completed=211,pending_new_references=report['pending_new_references'],blind_review_authorization='Explicit persistent user authorization; three history-free reviewers used',blockers=blockers,review_integration=str((ART/'review-integration.json').relative_to(ROOT)))
    for source in checkpoint['sources']:source['accepted_reference_units']=sum(r['source_id']==source['source_id'] and bool(r['accepted_label']) for r in new)
    save(ART/'checkpoint.json',checkpoint)
    overlay=read(ART/'source-registry-overlay.json');overlay['sources']=checkpoint['sources'];save(ART/'source-registry-overlay.json',overlay)
    print(json.dumps({k:v for k,v in report.items() if k not in ['input_manifest','blockers']},ensure_ascii=False))
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check-only',action='store_true');main(p.parse_args().check_only)
