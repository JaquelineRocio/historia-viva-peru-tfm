"""Validated, cumulative accounting for recovery-01; no inferred annotations."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / 'artifacts/beto-v3/recovery-01'
OUT = ROOT / 'outputs/beto-v3/recovery-01'
LEDGER = ROOT / 'artifacts/beto-v3/budget-ledger-current.json'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def immutable(p, obj):
    if p.exists():
        assert read(p) == obj, f'Immutable artifact changed: {p}'
    else:
        save(p, obj)


def responses():
    contract = META / 'integration-contract.json'
    if contract.exists():
        for item in read(contract)['items']:
            assert sha(ROOT / item['path']) == item['sha256'], f"Integration baseline altered: {item['path']}"
    prep = read(META / 'preparation.json')
    assert sha(OUT / 'candidates.json') == prep['candidates_sha256']
    assert sha(ROOT / prep['parent_dataset']) == prep['parent_sha256']
    guide = ROOT / 'docs/beto-v3/guia-etiquetado-v3.md'
    assert sha(guide) == prep['guide_sha256']
    units = {u['segment_id']: u for u in read(OUT / 'candidates.json')['items']}
    packets = {}
    for item in prep['packets']:
        p = ROOT / item['path']
        assert sha(p) == item['sha256']
        packet = read(p)
        assert packet['guide'] == guide.read_text(encoding='utf-8')
        for u in packet['items']:
            assert set(u) == {'segment_id', 'text', 'input_sha256', 'guide_sha256'}
            assert all(units[u['segment_id']][k] == v for k, v in u.items())
        packets[p.name] = packet
    labels = set(read(ROOT / 'artifacts/beto-v3/protocol.json')['labels']) | {None}
    results, manifests = {}, []
    for stage in ['first-pass', 'second-review']:
        result = {}
        for p in sorted((OUT / stage).glob('batch-*.json')):
            data = read(p)
            assert data['blind_context'] is True
            assert data['reviewer_session'] == ('recovery_first' if stage == 'first-pass' else 'recovery_second')
            expected = {u['segment_id'] for u in packets[p.name]['items']}
            assert len(data['items']) == len(expected)
            assert {r['segment_id'] for r in data['items']} == expected
            for r in data['items']:
                sid = r['segment_id']
                assert sid not in result
                u = units[sid]
                assert r['input_sha256'] == u['input_sha256']
                assert hashlib.sha256(u['text'].encode()).hexdigest() == u['input_sha256']
                assert r['guide_sha256'] == prep['guide_sha256']
                assert r['evidence'] and u['text'][slice(*r['evidence_span'])] == r['evidence']
                assert r['proposal'] in labels and r['alternative'] in labels
                assert r['accepted_label'] is None and r['training_eligible'] is False
                assert all(type(r[k]) is bool for k in ['ambiguous', 'extraction_defect', 'boundary_issue', 'boundary_blocking'])
                assert r['rationale'] and r['rule'] and r['boundary_rationale']
                assert r['model_weights'] == 'unknown'
                result[sid] = r
            manifests.append({'stage': stage, 'path': str(p.relative_to(ROOT)),
                              'sha256': sha(p), 'units': len(data['items']),
                              'session': data['reviewer_session']})
        results[stage] = result
    return units, results, manifests


def expected_ledger():
    units, results, manifests = responses()
    base = read(META / 'before/budget-ledger-current.json')
    assert base['new_unique_annotation_proposals'] == 938
    hashes = {r['input_sha256'] for group in results.values() for r in group.values()}
    expected = dict(base)
    expected.update(new_unique_annotation_proposals=938 + len(hashes),
                    annotation_budget_remaining=1200 - 938 - len(hashes),
                    recovery01_unique_annotation_inputs=len(hashes),
                    recovery01_first_pass_units=len(results['first-pass']),
                    recovery01_second_review_units=len(results['second-review']),
                    phase_B_second_review_units=base['phase_B_second_review_units'] + len(results['second-review']),
                    phase_B_second_review_batches=base['phase_B_second_review_batches'] + sum(m['stage'] == 'second-review' for m in manifests),
                    phase_B_second_review_calls=base['phase_B_second_review_calls'] + len({m['session'] for m in manifests if m['stage'] == 'second-review'}),
                    annotation_count_note='Preserved 938 historical inputs plus distinct recovery-01 hashes with actual saved proposals in either isolated pass; repeat passes add no unique input.')
    assert expected['annotation_budget_remaining'] >= 200
    assert not hashes & {u['input_sha256'] for u in read(ROOT / read(META / 'preparation.json')['parent_dataset'])['items']}
    return expected, units, results, manifests


def account(check_only=False):
    expected, units, results, manifests = expected_ledger()
    actual = read(LEDGER)
    event_map = {(m['stage'], Path(m['path']).name): m for m in manifests}
    for p in (META / 'response-events').glob('*/*.json'):
        assert (p.parent.name, p.name) in event_map, f'Previously accounted response removed: {p}'
        assert read(p) == event_map[(p.parent.name, p.name)], f'Previously accounted response altered: {p}'
    admission = ROOT / 'artifacts/beto-v3/admission-01/accounting-contract.json'
    if admission.exists():
        from beto_v3_admission_accounting import verify
        verify(expected)
        for item in manifests:
            assert read(META / 'response-events' / item['stage'] / Path(item['path']).name) == item
        # Historical integrations use their original ledger, never the newer total.
        return expected, units, results, manifests
    if check_only:
        assert actual == expected, 'Recovery cumulative ledger differs from real saved responses'
        for item in manifests:
            assert read(META / 'response-events' / item['stage'] / Path(item['path']).name) == item
    else:
        assert actual['new_unique_annotation_proposals'] <= expected['new_unique_annotation_proposals']
        for key in ['phase_B_second_review_units', 'phase_B_second_review_batches', 'phase_B_second_review_calls',
                    'recovery01_first_pass_units', 'recovery01_second_review_units']:
            assert actual.get(key, 0) <= expected[key], f'Counter cannot regress: {key}'
        base = read(META / 'before/budget-ledger-current.json')
        changed = set(expected) - set(base) | {k for k in base if expected[k] != base[k]}
        assert all(actual.get(k) == v for k, v in base.items() if k not in changed), 'Unrelated spend changed'
        for item in manifests:
            immutable(META / 'response-events' / item['stage'] / Path(item['path']).name, item)
        save(LEDGER, expected)
    return expected, units, results, manifests
