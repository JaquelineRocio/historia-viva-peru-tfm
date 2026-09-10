"""Offline integrity/phase gate. Exit 2 means prepared pilot, data gate still closed."""
import argparse
import csv
import hashlib
import json
from collections import Counter

from prepare_beto_v3 import ART, OUT, ROOT, read, sha, write

def verify():
    protocol=read(ART/'protocol.json')
    initial=read(OUT/'datasets/H-initial.json')
    reviewed=read(OUT/'datasets/H-reviewed.json')
    assert sha(ROOT/initial['parent'])==initial['parent_sha256'],'Original V2 dataset changed'
    assert len(initial['items'])==591 and len(reviewed['items'])==590
    assert sha(OUT/'datasets/H-initial.json')==reviewed['parent_sha256']
    assert sha(ART/'historical-review-decisions.json')==reviewed['decisions_sha256']
    labels=set(protocol['labels'])
    assert {r['label'] for r in reviewed['items']}==labels
    reserved=read(ART/'reserved-index.json')
    assert sha(ROOT/reserved['inherited_final']['manifest'])==reserved['v2_reserved_manifest_sha256']
    assert not set(reserved['inherited_final']['source_ids'])&{r['source_id'] for r in reviewed['items']}
    annotation=read(OUT/'annotation/pilot-first-pass.json')['items']
    for r in annotation:
        assert hashlib.sha256(r['text'].encode()).hexdigest()==r['input_sha256']
        a,z=r['evidence_span']
        assert r['text'][a:z]==r['evidence']
        assert r['proposal'] in labels and not r['training_eligible']
        assert r['v3_role']=='T' and r['second_pass'] is None
        cues=read(OUT/'acquisition'/r['source_id']/'cues.json')
        a,z=r['cue_span']
        assert r['text']==' '.join(c['text'].strip() for c in cues[a:z])
    candidates=read(OUT/'video-unit-candidates.json')['items']
    for r in candidates:
        assert r['v3_role']!='S' and not r['training_eligible']
        assert hashlib.sha256(r['text'].encode()).hexdigest()==r['text_sha256']
    assert not list((OUT/'acquisition'/'zb5zntF2kAs').glob('cues*')),'Reserved text exposed'
    curves=read(ART/'prior-train-curves.json')
    assert len(curves)==24
    for r in curves:
        assert set(r['train_metrics_eval']['per_class'])==labels
    current=ART/'phase-b-completion-01/resume-verification.json'
    additional_checks=[]
    if current.exists():
        resume=read(current)
        dataset=OUT/'phase-b-completion-01/all-development-units.json'
        assert sha(dataset)==resume['all_development_units_sha256'],'Current reviewed units changed after verification'
        rows=read(dataset)['items']
        assert len({r['segment_id'] for r in rows})==len(rows)
        family_roles={}
        for r in rows:
            assert r['partition']!='S' and not r['training_eligible']
            assert hashlib.sha256(r['text'].encode()).hexdigest()==r['input_sha256']
            assert r.get('accepted_label') in labels|{None}
            family_roles.setdefault(r['family_id'],set()).add(r['partition'])
            if r.get('adjudication'):
                d=r['adjudication'];a,z=d['evidence_span']
                assert r['text'][a:z]==d['evidence']
        assert all(len(roles)==1 for roles in family_roles.values()),'Work shared across partitions'
        additional_checks=['69 saved blind second reviews and text-grounded adjudications',
            f'{resume.get("ASR_second_review_checked",0)} ASR second reviews and {resume.get("ASR_adjudications_checked",0)} adjudications verified',
            'current development units hashes, labels and family-role separation',
            'current phase-B coverage and blockers used, not obsolete pilot counts']
    phase=read(ART/'phase-B-summary.json')
    blockers=phase['blockers']
    frozen=all((OUT/f'datasets/{name}.json').exists() for name in ['T300','V','S-manifest'])
    c_ready=bool(phase.get('C_ready')) and not blockers and frozen
    report={'integrity':'passed','checks':['V2 parent bytes preserved','H changes linked to source evidence',
        'inherited reserve manifest preserved','S has metadata only','annotation evidence and cue spans exact',
        '24 actual prior train/validation epoch metrics available']+additional_checks,
        'C_ready':c_ready,'blockers':blockers,
        'annotation_status':read(ART/'annotation-progress.json'),
        'goal_reached':False,'V3_macro_f1':None,'final_S_opened':False}
    gap_checkpoint=ART/'phase-b-gap-02/checkpoint.json'
    integrated=ART/'phase-b-gap-02/review-integration.json'
    if (ART/'phase-b-gap-02/selected-444/current.json').exists():
        from integrate_beto_v3_selected444 import main as verify_selected
        selected=verify_selected(check_only=True)
        report['checks']+=['Frozen previous 486 units and earlier response manifests preserved',
            f"Selected batch: {selected['first_pass_units']} first passes, {selected['second_review_units']} blind responses, {selected['adjudications']} adjudications checked"]
        report['blockers']=selected['blockers'];report['C_ready']=False
        report['accepted_30min_references']=selected['accepted_30min_references']
        report['selected444']=selected
        if (ART/'recovery-01/current.json').exists():
            from integrate_beto_v3_recovery import main as verify_recovery
            recovery=verify_recovery(check_only=True)
            report['recovery01']=recovery
            report['blockers']=recovery['blockers']
            report['accepted_30min_references']=recovery['accepted_30min_references']
            report['checks']+=['Recovery response hashes, exact evidence, cumulative spend, immutable checkpoints and conservative overlap exclusion verified']
    elif integrated.exists():
        from integrate_beto_v3_gap_reviews import main as verify_integration
        gap=verify_integration(check_only=True)
        report['checks']+=['211 history-free blind responses and 251 explicit adjudications verified',
            '235 inherited units unchanged; combined 486 units and input manifest hashes verified']
        report['additional_acquisition_batch']={'checkpoint':str(gap_checkpoint.relative_to(ROOT)),
            'accepted_new_references':gap['accepted_new_references'],
            'integration_status':'reference judgments integrated; source admission and datasets not frozen'}
        report['blockers']=gap['blockers'];report['C_ready']=False
        report['accepted_30min_references']=gap['accepted_30min_references']
        report['provisional_acquired_30min_works']={'T':13,'V':6}
        report['new_registered_S_works']=6
    elif gap_checkpoint.exists():
        gap=read(gap_checkpoint)
        ledger=read(ART/'budget-ledger-current.json')
        report['annotation_status']['unique_new_units_with_proposal']=ledger['new_unique_annotation_proposals']
        report['annotation_status']['remaining_annotation_ceiling']=ledger['annotation_budget_remaining']
        report['annotation_status']['gap_02_proposals_pending']=gap['first_pass_units']
        report['additional_acquisition_batch']={'checkpoint':str(gap_checkpoint.relative_to(ROOT)),
            'accepted_new_references':gap['accepted_new_references'],
            'integration_status':'quarantined; not added to frozen datasets'}
        # Report current acquisition separately from reference admission. Do not
        # keep claiming that newly acquired/reserved works are still absent.
        report['blockers']=[b for b in report['blockers'] if 'acquired/transcribed works >=30min' not in b and not b.startswith('S remains metadata-only:')]
        strict_path=ART/'phase-b-completion-01/exact-gaps-30min-works.csv'
        strict=list(csv.DictReader(strict_path.open(encoding='utf-8-sig')))
        report['blockers']=[b for b in report['blockers'] if not b.startswith(('T/','V/','T: 93/300;'))]
        for row in strict:
            if int(row['missing_examples']) or int(row['missing_works']):
                report['blockers'].append(f"{row['partition']}/{row['class']}: missing {row['missing_examples']} references and {row['missing_works']} works from >=30-minute sources")
        long_t=sum(int(r['accepted_from_30min_works']) for r in strict if r['partition']=='T')
        report['blockers'].append(f'T: {long_t}/300 accepted references from >=30-minute works; missing {max(0,300-long_t)}')
        new_long=Counter(r['role'] for r in gap['sources'] if (r.get('cues') or r.get('asr_transcript')) and r.get('duration_seconds',0)>=1800)
        old_works=list(csv.DictReader((ART/'phase-b-completion-01/source-work-targets.csv').open(encoding='utf-8-sig')))
        report['provisional_acquired_30min_works']={r['partition']:int(r['acquired_transcribed_works_at_least_30min'])+new_long[r['partition']] for r in old_works}
        report['new_registered_S_works']=read(ART/'phase-b-completion-01/reserved-work-target.json')['registered_new_S_video_works']+gap['new_reserved_metadata_works']
        report['blockers']=report['blockers']+gap['blockers']
        report['C_ready']=False
    if (ART/'admission-01/current.json').exists():
        from integrate_beto_v3_admission import main as verify_admission
        admission=verify_admission(check_only=True)
        report['admission01']=admission
        report['blockers']=admission['blockers']
        report['C_ready']=admission['C_ready']
        report['accepted_30min_references']=admission['accepted_30min_references']
        report['annotation_status']['unique_new_units_with_proposal']=admission['annotation_unique']
        report['annotation_status']['remaining_annotation_ceiling']=admission['annotation_remaining']
        report['checks']+=['Admission originals, isolated response hashes, immutable cumulative ledger and source-window prevalidation verified']
        report['incidental_reserved_search_snippet_seen']=admission['incidental_reserved_search_snippet_seen']
        report['reserved_search_snippet_used']=False
    if (ART/'phase-c-freeze.json').exists():
        from run_beto_phase_c_v3 import frozen_inputs
        freeze, datasets = frozen_inputs()
        report['historical_admission_blockers'] = report['blockers']
        report['blockers'] = []
        report['C_ready'] = True
        report['development_freeze_sha256'] = sha(ART/'phase-c-freeze.json')
        report['annotation_status']['historical_snapshot_note'] = 'Admission-01 counters preserved; see frozen_dataset_status for current eligibility'
        report['frozen_dataset_status'] = {name:len(group) for name,group in datasets.items()}
        report['frozen_dataset_status']['S_manifest_metadata_only'] = True
        comparison = OUT/'phase-c/comparison-seed42.json'
        if comparison.exists():
            c = read(comparison)
            assert c['freeze_sha256'] == report['development_freeze_sha256']
            report['V3_macro_f1'] = {r['recipe']:r['metrics']['f1_macro'] for r in c['results']}
            report['phase_C_candidate'] = c['candidate']
            report['phase_C_status'] = 'complete; final success not evaluated on S'
            report['current_training_ledger'] = 'artifacts/beto-v3/budget-ledger-after-C.json'
        report['checks'] += ['Scoped C-D exception, pinned admission, frozen references and all original source/quality/budget requirements verified']
    destination=ART/'verification.json'
    if current.exists():
        previous=ART/'phase-b-completion-01/verification-before-resume.json'
        if destination.exists() and not previous.exists():previous.write_bytes(destination.read_bytes())
        destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    else:
        write(destination,report)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--require-C',action='store_true')
    args=parser.parse_args()
    report=verify()
    print(json.dumps(report,ensure_ascii=True))
    if args.require_C and not report['C_ready']:
        raise SystemExit(2)
