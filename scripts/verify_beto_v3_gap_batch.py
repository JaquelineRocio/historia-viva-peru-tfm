"""Offline verification of new sources, unchanged parents, budgets and blind queues."""
import hashlib, json, re
from collections import Counter
from acquire_beto_v3_gap_batch import ROOT,DEST,ART,read,save
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=read(ART/'acquisition-plan.json');registry=read(ROOT/'artifacts/beto-v3/phase-b-completion-01/source-registry-final.json')
    old_roles={r['video_id']:r.get('role',r.get('proposed_role')) for r in registry['existing_sources']+registry['new_candidates'] if r.get('video_id')}
    reserved=read(ART/'reserve-metadata.json')['sources']
    reserved_ids={r['video_id'] for r in reserved}|{v for v,r in old_roles.items() if r=='S'}
    assert not reserved_ids&{r['video_id'] for r in plan['sources']}
    assert all(r['role']!='S' and old_roles.get(r['video_id'],r['role'])==r['role'] for r in plan['sources'])
    legacy_reserved=read(ROOT/'artifacts/beto-v3/reserved-index.json')
    assert sha(ROOT/legacy_reserved['inherited_final']['manifest'])==legacy_reserved['v2_reserved_manifest_sha256']
    stats=[];hashes=set();checks=0
    for r in plan['sources']:
        folder=DEST/r['source_id'];receipt=read(folder/'receipt.json')
        assert receipt['role']==r['role'] and not receipt['training_eligible']
        path=folder/'cues.json';method='public_captions'
        if not path.exists():path=folder/'asr/cues.json';method='local_ASR'
        if not path.exists():continue
        cues=read(path)
        if method=='public_captions':assert sha(path)==receipt['captions_sha256']
        else:
            t=read(folder/'asr/transcription.json');assert t['complete_audio_processed'] and t['segments']==cues
            assert read(folder/'download.json')['integrity_decode_ok']
        units=read(folder/'annotation/units.json')['items'];idx={u['segment_id']:u for u in units}
        if method=='public_captions':
            assert sorted(i for u in units for i in u['cue_indices'])==list(range(len(cues)))
            assert all(u['text']==re.sub(r'\s+',' ',' '.join(cues[i]['text'].strip() for i in u['cue_indices'] if cues[i]['text'].strip())).strip() for u in units)
        else:assert ''.join(u['text_original'] for u in units)==' '.join(c['text'].strip() for c in cues)
        for u in units:
            assert u['partition']==r['role'] and not u['training_eligible'] and sha(path)==u['source_sha256']
            assert hashlib.sha256(u['text'].encode()).hexdigest()==u['input_sha256']
            assert u['tokens_with_specials']<=384 and u['would_truncate_tokens']==0
        first=[u for p in (folder/'annotation/first-pass').glob('batch-*.json') for u in read(p)['items']]
        first += [u for p in (DEST/'selected-444/first-pass').glob('batch-*.json') for u in read(p)['items'] if u['segment_id'] in idx]
        for u in first:
            original=idx[u['segment_id']];assert u['input_sha256']==original['input_sha256']
            assert original['text'][slice(*u['evidence_span'])]==u['evidence']
            assert u['accepted_label'] is None and not u['training_eligible'];hashes.add(u['input_sha256']);checks+=1
        stats.append(dict(source_id=r['source_id'],role=r['role'],duration_seconds=receipt['duration_seconds'],method=method,units=len(units),first_pass=len(first),reviewed_accepted=0))
    ledger=read(ROOT/'artifacts/beto-v3/budget-ledger-current.json');baseline=read(ART/'budget-before-gap-02.json')
    recovery_inputs=0
    if ledger.get('recovery01_unique_annotation_inputs',0):
        from beto_v3_recovery_accounting import account
        checked,_,_,_=account(check_only=True)
        recovery_inputs=checked['recovery01_unique_annotation_inputs']
    admission_inputs=0
    if (ROOT/'artifacts/beto-v3/admission-01/accounting-contract.json').exists():
        from beto_v3_admission_accounting import verify
        latest=verify()
        admission_inputs=latest.get('admission01_unique_annotation_inputs',0)
    assert ledger['new_unique_annotation_proposals']==baseline['new_unique_annotation_proposals']+len(hashes)+recovery_inputs+admission_inputs<=1200
    assert ledger['annotation_budget_remaining']==1200-ledger['new_unique_annotation_proposals']
    assert ledger['ASR_gpu_seconds']<=28800 and ledger['services_paid_USD']==0 and ledger['new_training_trajectories']==0
    queue=read(ART/'blind-review-queue.json');blind=[]
    for path in queue['batches']:
        b=read(ROOT/path)['items'];assert all(not {'proposal','alternative','rationale','accepted_label'}&set(u) for u in b);blind+=b
    assert len(blind)==queue['units'] and len({u['segment_id'] for u in blind})==len(blind)
    report=dict(integrity='passed',sources=stats,acquired_long_work_counts_provisional=dict(Counter(r['role'] for r in stats if r['duration_seconds']>=1800)),first_pass_evidence_checks=checks,blind_inputs=len(blind),new_reserved_metadata_works=len(reserved),new_reference_gains=0,S_content_opened=False,C_ready=False,ledger_sha256=sha(ROOT/'artifacts/beto-v3/budget-ledger-current.json'),limitations=['References await blind review and discourse adjudication','Full caption inventory verified, literal audio fidelity not certified','Acquired work counts provisional until final source admission'])
    if (ART/'selected-444/current.json').exists():
        from integrate_beto_v3_selected444 import main as integrated
        integration=integrated(check_only=True)
        report['new_reference_gains']=237+integration['accepted_new_references']
        report['blind_second_reviews_checked']=211+integration['second_review_units']
        report['inherited_gap_blind_inputs']=211
        report['selected444_blind_inputs']=integration['second_review_target']
        report['blind_inputs']=211+integration['second_review_target']
        report['adjudications_checked']=251+integration['adjudications']
        report['limitations'][0]='Final source admission, class quotas, coverage and freezing remain pending'
        accepted=Counter(r['source_id'] for path in [DEST/'new-reviewed-units.json',DEST/'selected-444/new-reviewed-units.json'] for r in read(path)['items'] if r['accepted_label'])
        for source in report['sources']:source['reviewed_accepted']=accepted[source['source_id']]
    elif (ART/'review-integration.json').exists():
        from integrate_beto_v3_gap_reviews import main as integrated
        integration=integrated(check_only=True)
        report['new_reference_gains']=integration['accepted_new_references']
        report['blind_second_reviews_checked']=211;report['adjudications_checked']=251
        report['limitations'][0]='Reference judgments integrated; final source admission and freezing still pending'
        accepted=Counter(r['source_id'] for r in read(DEST/'new-reviewed-units.json')['items'] if r['accepted_label'])
        for source in report['sources']:source['reviewed_accepted']=accepted[source['source_id']]
    save(ART/'verification.json',report);print(json.dumps({k:v for k,v in report.items() if k!='sources'},ensure_ascii=False))
if __name__=='__main__':main()
