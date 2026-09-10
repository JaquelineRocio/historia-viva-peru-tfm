"""Integrate actual recovery judgments without duplicate reference gains."""
import argparse
import hashlib
import json
from collections import Counter

from beto_v3_recovery_accounting import ROOT, META, OUT, account, read, save, sha, immutable


def choose_effective(old, units, decisions):
    """Prior accepted intervals win; adjudication alone never authorizes duplicates."""
    old_by_id = {u['segment_id']: u for u in old}
    selected, disposition = [], {}
    for sid, u in sorted(units.items()):
        d = decisions.get(sid)
        if not d or d['resolved_label'] is None:
            disposition[sid] = {'status': 'pending_reference', 'conflicts': []}
            continue
        assert not old_by_id[u['parent_segment_id']].get('accepted_label')
        conflicts = [k for k in u['overlapping_existing_ids'] if old_by_id[k].get('accepted_label')]
        a, z = u['source_char_span']
        conflicts += [v['segment_id'] for v in selected if v['source_id'] == u['source_id']
                      and v['source_char_span'][0] < z and v['source_char_span'][1] > a]
        if conflicts:
            disposition[sid] = {'status': 'resolved_but_excluded_overlap', 'conflicts': sorted(conflicts)}
        else:
            selected.append(u)
            disposition[sid] = {'status': 'accepted_replacement_of_pending_parent', 'conflicts': []}
    return selected, disposition


def main(check_only=False):
    admission = ROOT / 'artifacts/beto-v3/admission-01/accounting-contract.json'
    if admission.exists() and not check_only:
        return main(check_only=True)
    # Reject edits/removal of previously checkpointed judgments before publishing.
    for checkpoint_manifest in (META / 'checkpoints').glob('*/response-manifest.json'):
        for item in read(checkpoint_manifest)['items']:
            assert sha(ROOT / item['path']) == item['sha256'], f"Checkpointed response changed: {item['path']}"
    ledger, units, reviews, manifest = account(check_only=check_only)
    prep = read(META / 'preparation.json')
    parent = ROOT / prep['parent_dataset']
    old = read(parent)['items']
    assert sha(parent) == prep['parent_sha256']
    for item in prep['source_manifest']:
        assert sha(ROOT / item['path']) == item['sha256']
    audit = read(META / 'overlap-audit.json')
    for item in audit['provenance'].values():
        for source in item if isinstance(item, list) else [item]:
            assert sha(ROOT / source['path']) == source['sha256']
    audited = {r['segment_id']: r for r in audit['items']}
    assert set(audited) == set(units)
    for sid, u in units.items():
        assert set(u['overlapping_existing_ids']) == {r['segment_id'] for r in audited[sid]['existing_overlaps']}
    first, second = reviews['first-pass'], reviews['second-review']
    labels = set(read(ROOT / 'artifacts/beto-v3/protocol.json')['labels']) | {None}
    decisions = {}
    for p in sorted((OUT / 'adjudication').glob('batch-*.json')):
        packet = read(OUT / 'inputs' / p.name)
        data = read(p)
        assert data['parent_signoff'] is True
        assert len(data['items']) == len(packet['items'])
        assert {r['segment_id'] for r in data['items']} == {r['segment_id'] for r in packet['items']}
        for d in data['items']:
            sid = d['segment_id']
            assert sid not in decisions and sid in first and sid in second
            u = units[sid]
            assert d['resolved_label'] in labels and d['accepted_label'] is None
            assert d['input_sha256'] == u['input_sha256'] and d['guide_sha256'] == u['guide_sha256']
            assert d['evidence'] and u['text'][slice(*d['evidence_span'])] == d['evidence']
            assert d['evidence_checked'] and d['boundary_checked']
            assert not d['training_eligible'] and d['rationale']
            if d['resolved_label'] is not None:
                assert not d['boundary_blocking']
            assert d['first_response_sha256'] == hashlib.sha256(json.dumps(first[sid], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            assert d['second_response_sha256'] == hashlib.sha256(json.dumps(second[sid], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            decisions[sid] = d
        manifest.append({'stage': 'adjudication', 'path': str(p.relative_to(ROOT)), 'sha256': sha(p), 'units': len(data['items']), 'session': 'parent'})
    selected, disposition = choose_effective(old, units, decisions)
    records = []
    for sid, u in sorted(units.items()):
        records.append({**u, 'first_pass': first.get(sid), 'second_review': second.get(sid),
                        'adjudication': decisions.get(sid), 'integration': disposition[sid]})
    replaced = {u['parent_segment_id'] for u in selected}
    effective = [r for r in old if r['segment_id'] not in replaced]
    for u in selected:
        sid = u['segment_id']
        effective.append({**u, 'first_pass': first[sid], 'second_review': second[sid],
                          'adjudication': decisions[sid], 'accepted_label': decisions[sid]['resolved_label'],
                          'reference_status': 'accepted_reference', 'source_admission': 'pending_final_work_admission'})
    assert len(effective) == len(old)
    assert all(not r['training_eligible'] and r['partition'] != 'S' for r in effective)
    from integrate_beto_v3_selected444 import coverage
    gaps, works = coverage(effective)
    accepted = dict(Counter(r['partition'] for r in effective if r.get('accepted_label')))
    previous = read(ROOT / 'artifacts/beto-v3/phase-b-gap-02/selected-444/current.json')
    blockers = [f"{r['partition']}/{r['class']}: missing {r['missing_examples']} references and {r['missing_works']} works from >=30-minute sources" for r in gaps if r['missing_examples'] or r['missing_works']]
    blockers += [b for b in previous['blockers'] if not b.startswith(('T/', 'V/'))]
    if len(decisions) < len(units):
        blockers.append(f"Recovery: {len(units)-len(decisions)} candidate adjudications outstanding")
    summary = {**previous, 'version': 'recovery-01-v1',
        'recovery_first_pass': len(first), 'recovery_second_review': len(second),
        'recovery_adjudications': len(decisions), 'recovery_complete': len(decisions) == len(units),
        'recovery_resolved_judgments': sum(d['resolved_label'] is not None for d in decisions.values()),
        'recovery_pending_judgments': sum(d['resolved_label'] is None for d in decisions.values()),
        'recovery_overlap_excluded': sum(d['status'] == 'resolved_but_excluded_overlap' for d in disposition.values()),
        'recovery_effective_gains': len(selected), 'replaced_pending_ids': sorted(replaced),
        'accepted_references': accepted,
        'accepted_30min_references': {role: sum(r['accepted_from_30min_works'] for r in gaps if r['partition'] == role) for role in ['T', 'V']},
        'pending_references': sum(not r.get('accepted_label') for r in effective),
        'annotation_unique': ledger['new_unique_annotation_proposals'], 'annotation_remaining': ledger['annotation_budget_remaining'],
        'second_review_units_cumulative': ledger['phase_B_second_review_units'],
        'recovery_label_agreements': sum(first[k]['proposal'] == second[k]['proposal'] for k in set(first) & set(second)),
        'recovery_label_disagreements': sum(first[k]['proposal'] != second[k]['proposal'] for k in set(first) & set(second)),
        'blockers': blockers, 'C_ready': False, 'S_content_opened': False,
        'all_development_units': str((OUT / 'all-development-units.json').relative_to(ROOT)),
        'reference_note': 'AI-assisted judgments, not expert gold; same family in isolated sessions, provider weights unknown; only disjoint effective replacements count.',
        'source_registry_overlay': previous['source_registry_overlay'],
        'source_registry_overlay_note': 'Inherited source admission metadata; current reference counts in recovery coverage files.'}
    summary['coverage'] = {role: {'accepted': accepted[role], 'units': sum(r['partition'] == role for r in effective),
                                  'fraction': accepted[role]/sum(r['partition'] == role for r in effective)} for role in ['T', 'V']}
    objects = {
        OUT / 'reviewed-candidates.json': {'items': records},
        OUT / 'all-development-units.json': {'parent': str(parent.relative_to(ROOT)), 'parent_sha256': sha(parent), 'items': effective},
        OUT / 'pending-resolution.json': {'items': [r for r in effective if not r.get('accepted_label')]},
        META / 'exact-gaps.json': {'items': gaps}, META / 'coverage-by-work.json': {'items': works},
        META / 'response-manifest.json': {'items': manifest}}
    for stage, responses in reviews.items():
        cache = []
        for sid, response in sorted(responses.items()):
            key = {'stage': stage, 'input_sha256': response['input_sha256'], 'context': None,
                   'guide_sha256': response['guide_sha256'], 'model': response['model'],
                   'model_weights': response['model_weights'], 'prompt_version': response['prompt_version'],
                   'configuration': response['exposed_configuration']}
            cache.append({'segment_id': sid, 'key': key,
                          'cache_key_sha256': hashlib.sha256(json.dumps(key, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                          'response_sha256': hashlib.sha256(json.dumps(response, ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
        objects[META / (stage+'-cache.json')] = {'items': cache}
    for p, obj in objects.items():
        if check_only:
            assert read(p) == obj, f'Derived artifact differs: {p}'
        else:
            save(p, obj)
    summary['all_development_units_sha256'] = sha(OUT / 'all-development-units.json')
    ap = {**read(META / 'before/annotation-progress.json'),
          'unique_new_units_with_proposal': ledger['new_unique_annotation_proposals'],
          'remaining_annotation_ceiling': ledger['annotation_budget_remaining'],
          'second_review_units': ledger['phase_B_second_review_units'],
          'accepted_references': accepted, 'pending': summary['pending_references'],
          'recovery_first_pass': len(first), 'recovery_second_review': len(second),
          'recovery_adjudications': len(decisions), 'recovery_effective_gains': len(selected)}
    for p, obj in [(META/'current.json', summary), (ROOT/'artifacts/beto-v3/phase-B-summary.json', summary),
                   (ROOT/'artifacts/beto-v3/annotation-progress.json', ap)]:
        if check_only:
            historical = p
            if admission.exists() and p.parent == ROOT/'artifacts/beto-v3':
                historical = admission.parent / 'before' / p.name
            assert read(historical) == obj, f'Current/historical report differs: {historical}'
        else:
            save(p, obj)
    cp = META / 'checkpoints' / f"{len(first):03}-{len(second):03}-{len(decisions):03}"
    for name, obj in [('summary.json', summary), ('budget-ledger.json', ledger), ('response-manifest.json', {'items': manifest})]:
        if check_only:
            assert read(cp / name) == obj
        else:
            immutable(cp / name, obj)
    print(json.dumps({k: summary[k] for k in ['recovery_first_pass', 'recovery_second_review', 'recovery_adjudications', 'recovery_effective_gains', 'annotation_unique', 'annotation_remaining', 'C_ready']}))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-only', action='store_true')
    main(parser.parse_args().check_only)
