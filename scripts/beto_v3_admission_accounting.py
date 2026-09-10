"""Admission continuation: immutable recovery baseline plus authentic new events."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts/beto-v3/admission-01'
OUT = ROOT / 'outputs/beto-v3/admission-01'
CONTRACT = ART / 'accounting-contract.json'
LEDGER = ROOT / 'artifacts/beto-v3/budget-ledger-current.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def immutable(path, value):
    if path.exists():
        assert read(path) == value, f'Immutable admission artifact changed: {path}'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write('\n')


def initialize():
    """One-time capture after all ASR reservations settle; never writes ledger."""
    from beto_v3_recovery_accounting import expected_ledger
    recovery, _, _, _ = expected_ledger()
    windows = sorted(OUT.glob('*/asr/window-*.json'))
    setups = sorted(ART.glob('asr-setup-samples-*.json'))
    assert windows and setups
    seconds = []
    receipts = []
    for path in setups:
        record = read(path)
        assert record['budget_accounted'] is True and record['load_wall_seconds'] >= 0
        seconds.append(record['load_wall_seconds'])
        receipts.append({**entry(path), 'kind': 'model_load', 'seconds': record['load_wall_seconds']})
    alias = ART / 'asr-setup-samples.json'
    if alias.exists():
        assert any(read(alias) == read(path) for path in setups), 'Unmatched setup alias'
    for path in windows:
        record = read(path)
        assert 'wall_seconds' in record, 'ASR reservation still in flight; settle before checking'
        assert record['wall_seconds'] >= 0
        source = path.parent.parent / 'download.json'
        assert read(source)['sha256'] == record['source_sha256']
        seconds.append(record['wall_seconds'])
        receipts.append({**entry(path), 'kind': 'ASR_window', 'seconds': record['wall_seconds'],
                         'acquisition': entry(source)})
    actual = read(LEDGER)
    derived = {**recovery, 'ASR_gpu_seconds': recovery['ASR_gpu_seconds'] + math.fsum(seconds)}
    assert all(actual[k] == v for k, v in derived.items() if k != 'ASR_gpu_seconds')
    assert set(actual) == set(derived), 'Unexpected new counters before admission baseline'
    assert math.isclose(actual['ASR_gpu_seconds'], derived['ASR_gpu_seconds'], rel_tol=0, abs_tol=1e-8)
    assert actual['ASR_gpu_seconds'] <= 28800
    immutable(ART / 'before/recovery-ledger.json', recovery)
    # Retain the actual IEEE float after reconciling it against measured receipts.
    immutable(ART / 'before/budget-ledger-current.json', actual)
    snapshots = []
    for name in ('phase-B-summary.json', 'annotation-progress.json'):
        source = ROOT / 'artifacts/beto-v3' / name
        target = ART / 'before' / name
        immutable(target, read(source))
        snapshots.append(entry(target))
    contract = dict(version='admission-accounting-01',
                    recovery_ledger=entry(ART / 'before/recovery-ledger.json'),
                    admission_baseline=entry(ART / 'before/budget-ledger-current.json'),
                    historical_reports=snapshots, ASR_receipts=receipts,
                    measured_new_ASR_seconds=math.fsum(seconds),
                    float_roundoff_seconds=actual['ASR_gpu_seconds'] - derived['ASR_gpu_seconds'],
                    excluded_alias=entry(alias) if alias.exists() else None,
                    reserved_S_annotations=200, maximum_new_development_annotations=31)
    immutable(CONTRACT, contract)
    return contract


def checked(path_entry):
    path = (ROOT / path_entry['path']).resolve()
    assert path.is_relative_to(ROOT) and sha(path) == path_entry['sha256'], f'Admission receipt altered: {path}'
    return read(path)


def expected_ledger(recovery=None):
    contract = read(CONTRACT)
    historical = checked(contract['recovery_ledger'])
    if recovery is not None:
        assert historical == recovery, 'Recovery history changed after admission began'
    baseline = checked(contract['admission_baseline'])
    for receipt in contract['historical_reports']:
        checked(receipt)
    observed = []
    for receipt in contract['ASR_receipts']:
        record = checked(receipt)
        seconds = record['load_wall_seconds'] if receipt['kind'] == 'model_load' else record['wall_seconds']
        assert seconds == receipt['seconds']
        observed.append(seconds)
        if 'acquisition' in receipt:
            assert checked(receipt['acquisition'])['sha256'] == record['source_sha256']
    assert math.fsum(observed) == contract['measured_new_ASR_seconds']
    assert math.isclose(baseline['ASR_gpu_seconds'], historical['ASR_gpu_seconds'] + math.fsum(observed), rel_tol=0, abs_tol=1e-8)
    assert {k: v for k, v in baseline.items() if k != 'ASR_gpu_seconds'} == {k: v for k, v in historical.items() if k != 'ASR_gpu_seconds'}
    # Reject unrecorded ASR receipts, rather than silently dropping fresh spending.
    live = {str(p.relative_to(ROOT)) for p in list(OUT.glob('*/asr/window-*.json')) + list(ART.glob('asr-setup-samples-*.json'))}
    assert live == {r['path'] for r in contract['ASR_receipts']}, 'New ASR events need a new versioned accounting contract'
    if contract['excluded_alias']:
        checked(contract['excluded_alias'])
    expected = dict(baseline)
    annotation = ART / 'annotation-accounting.json'
    assert annotation.exists() or not list((ART / 'annotation-events').glob('*.json')), 'Previously accounted annotation manifest removed'
    if annotation.exists():
        manifest = read(annotation)
        assert manifest['baseline_sha256'] == contract['admission_baseline']['sha256']
        archived = {read(p)['path']: read(p) for p in (ART / 'annotation-events').glob('*.json')}
        current = {r['path']: r for r in manifest['response_files']}
        assert all(current.get(path) == receipt for path, receipt in archived.items()), 'Previously accounted admission response removed or changed'
        hashes, first, second, sessions, batches = set(), set(), set(), set(), set()
        paths = set()
        previous = read(ROOT / 'outputs/beto-v3/recovery-01/all-development-units.json')['items']
        previous += read(ROOT / 'outputs/beto-v3/recovery-01/candidates.json')['items']
        known = {r['input_sha256'] for r in previous}
        for receipt in manifest['response_files']:
            assert receipt['path'] not in paths, 'Response file counted twice'
            paths.add(receipt['path'])
            data = checked(receipt)
            assert receipt['stage'] in ('first-pass', 'second-review') and data['items']
            group = first if receipt['stage'] == 'first-pass' else second
            for response in data['items']:
                digest = response['input_sha256']
                assert digest not in known, 'Admission input already counted historically'
                assert len(digest) == 64 and 'proposal' in response and response.get('evidence')
                hashes.add(digest)
                group.add(digest)
            if receipt['stage'] == 'second-review':
                batches.add(receipt['path'])
                sessions.add(receipt['session'])
        assert len(hashes) <= contract['maximum_new_development_annotations']
        expected.update(new_unique_annotation_proposals=baseline['new_unique_annotation_proposals'] + len(hashes),
                        annotation_budget_remaining=baseline['annotation_budget_remaining'] - len(hashes),
                        phase_B_second_review_units=baseline['phase_B_second_review_units'] + len(second),
                        phase_B_second_review_batches=baseline['phase_B_second_review_batches'] + len(batches),
                        phase_B_second_review_calls=baseline['phase_B_second_review_calls'] + len(sessions),
                        admission01_unique_annotation_inputs=len(hashes), admission01_first_pass_units=len(first),
                        admission01_second_review_units=len(second))
        assert expected['annotation_budget_remaining'] >= contract['reserved_S_annotations']
    return expected


def record_response_events():
    """Integrator calls after writing manifest and before publishing derived ledger."""
    expected_ledger()
    manifest = read(ART / 'annotation-accounting.json')
    for receipt in manifest['response_files']:
        name = hashlib.sha256(receipt['path'].encode()).hexdigest() + '.json'
        immutable(ART / 'annotation-events' / name, receipt)


def verify(recovery=None):
    expected = expected_ledger(recovery)
    annotation = ART / 'annotation-accounting.json'
    if annotation.exists():
        for receipt in read(annotation)['response_files']:
            name = hashlib.sha256(receipt['path'].encode()).hexdigest() + '.json'
            assert read(ART / 'annotation-events' / name) == receipt, 'Missing immutable response event'
    assert read(LEDGER) == expected, 'Admission ledger differs from immutable baseline plus real response events'
    return expected


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--initialize', action='store_true')
    args = parser.parse_args()
    if args.initialize:
        initialize()
    print(json.dumps(verify(), indent=2))
