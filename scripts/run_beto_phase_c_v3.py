"""Fail-closed R0-R3 orchestration. Never acquires or opens reserved text."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import time
import uuid
import shutil

import beto_phase_c_core_v3 as core
from run_beto_first_training_v2 import (
    ROOT, LABELS, BASE, REV, read, save, filehash, fingerprint, metrics, verify_result,
)

ART = ROOT / 'artifacts/beto-v3'
OUT = ROOT / 'outputs/beto-v3/phase-c'
FREEZE = ART / 'phase-c-freeze.json'
EXPECTED = {'R0': (['H'], 2e-5, 4), 'R1': (['H', 'T300'], 2e-5, 4),
            'R2': (['H', 'T300'], 2e-5, 20), 'R3': (['H', 'T300'], 1e-5, 20)}


def require(value, message):
    if not value:
        raise ValueError(message)


def pinned(entry):
    path = (ROOT / entry['path']).resolve()
    require(path.is_relative_to(ROOT), 'Pinned path outside project')
    require(filehash(path) == entry['sha256'], 'Frozen bytes changed: ' + str(path))
    return path


def protocol_check():
    p = read(ART / 'protocol.json')
    require(p['labels'] == LABELS and p['base_model'] == BASE and p['revision'] == REV,
            'Protocol model/labels differ')
    require(p['max_length'] == 384, 'Length must remain 384')
    for name, (data, lr, epochs) in EXPECTED.items():
        require(p['recipes'][name] == dict(data=data, lr=lr, epochs=epochs), 'Recipe differs: ' + name)
    expected = dict(microbatch=2, gradient_accumulation=8, effective_batch=16,
                    optimizer='AdamW', weight_decay=.01, clip_norm=1.,
                    precision='AMP float16', warmup_ratio=.1,
                    scheduler='linear; fresh horizon for each trajectory',
                    class_weights='inverse_frequency_train_only',
                    loss_normalization='sum_weighted_CE / sum_weights_effective_batch')
    require(p['recipe'] == expected, 'Core does not implement changed recipe')
    require(filehash(ROOT / 'docs/beto-v3/plan-beto-f1-070.md') == p['plan_sha256'], 'Plan hash changed')
    for package, version in p['versions'].items():
        require(importlib.metadata.version(package) == version, 'Environment differs: ' + package)
    from huggingface_hub.constants import HF_HUB_CACHE
    base = Path(HF_HUB_CACHE) / ('models--' + BASE.replace('/', '--')) / 'snapshots' / REV
    for name, digest in p['base_hashes'].items():
        require(filehash(base / name) == digest, 'Cached base differs: ' + name)
    return p


def normalized_rows(document, partition):
    role = 'T' if partition == 'T300' else partition
    require(document.get('frozen') is True and document['partition'] == role,
            'Dataset must explicitly be frozen: ' + partition)
    result = []
    for row in document['items']:
        require(row.get('v3_role', row.get('partition')) == role, 'Wrong row partition')
        label = row.get('accepted_label', row.get('label'))
        eligibility = row.get('reference_eligible') if partition == 'V' else row.get('training_eligible')
        require(label in LABELS and eligibility is True,
                'Unresolved/ineligible frozen reference: ' + row['segment_id'])
        digest = __import__('hashlib').sha256(row['text'].encode()).hexdigest()
        require(digest == row.get('input_sha256', row.get('text_sha256')), 'Input text hash differs')
        result.append({**row, 'label': label, 'text_sha256': digest,
                       'role': 'historical_train' if partition == 'H' else 'new_AI'})
    require(len({r['segment_id'] for r in result}) == len(result), 'Duplicate row IDs')
    require(len({r['text_sha256'] for r in result}) == len(result), 'Duplicate input texts')
    return result


def frozen_inputs():
    require(FREEZE.exists(), 'Phase C closed: no phase-c-freeze.json')
    freeze = read(FREEZE)
    require(freeze.get('C_ready') is True and freeze.get('blockers') == []
            and freeze.get('admission_completed') is True and freeze.get('S_closed') is True,
            'Phase C closed: admission or blockers unresolved')
    require(freeze['protocol_sha256'] == filehash(ART / 'protocol.json'), 'Freeze protocol differs')
    overrides = {}
    if 'development_contract' in freeze:
        contract = read(pinned(freeze['development_contract']))
        p = read(ART / 'protocol.json')
        require(contract['scope'] == ['C', 'D'] and contract['partition'] == 'V'
                and contract['S_closed'] is True, 'Exception scope differs')
        require(contract['original_budget'] == p['budget']
                and contract['original_success'] == p['evaluation']['targets']
                and contract['labels'] == LABELS, 'Exception altered protected requirements')
        pinned(contract['protocol']); pinned(contract['plan_amendment']); pinned(contract['admission'])
        overrides = contract['minimum_overrides']
        require(overrides == {'contexto_colonial_antecedentes': 23,
                              'organizacion_consecuencias_republicanas': 23}, 'Unapproved coverage exception')
        require(contract['original_operational_goal'] == 25 and contract['operational_goal_met'] is False,
                'Original operational target must remain explicit')
        require(all(n >= p['evaluation']['targets']['resolvable_reference_coverage']
                    for n in contract['reference_coverage'].values()), 'Resolvable coverage below original threshold')
    # Hash receipts; their substantive admission is a prerequisite, not inferred here.
    require(bool(freeze.get('admission_evidence')), 'No admission evidence pinned')
    for entry in freeze['admission_evidence']:
        pinned(entry)
    require(freeze.get('representation') == 'normalized_authentic_target_only', 'Representation differs')
    paths = {name: pinned(freeze['datasets'][name]) for name in ('H', 'T300', 'V', 'S-manifest')}
    reserved = read(paths['S-manifest'])  # Metadata manifest only; no content paths followed.
    require(reserved.get('metadata_only') is True and reserved.get('frozen') is True,
            'S manifest must be frozen metadata only')
    def metadata_only(value):
        if isinstance(value, dict):
            return not {'text', 'text_original', 'label', 'accepted_label', 'transcript', 'cues'} & value.keys() and all(metadata_only(v) for v in value.values())
        return not isinstance(value, list) or all(metadata_only(v) for v in value)
    require(metadata_only(reserved),
            'S manifest contains content')
    require(bool(reserved.get('family_ids')) and bool(reserved.get('source_ids')), 'Missing S identities')
    rows = {name: normalized_rows(read(paths[name]), name) for name in ('H', 'T300', 'V')}
    for left, right in (('H', 'T300'), ('H', 'V'), ('T300', 'V')):
        for key in ('segment_id', 'text_sha256', 'family_id', 'source_id'):
            require(not {r[key] for r in rows[left]} & {r[key] for r in rows[right]}, 'Partition overlap: ' + key)
    for group in rows.values():
        require(not {r['family_id'] for r in group} & set(reserved['family_ids']), 'S family leakage')
        require(not {r['source_id'] for r in group} & set(reserved['source_ids']), 'S source leakage')
    for name, minimum in (('T300', 20), ('V', 25)):
        require(len(rows[name]) >= (300 if name == 'T300' else 175), 'Insufficient frozen references')
        for label in LABELS:
            eligible = [r for r in rows[name] if r['label'] == label and r.get('duration_seconds', 0) >= 1800]
            target = overrides.get(label, minimum) if name == 'V' else minimum
            require(len(eligible) >= target and len({r['family_id'] for r in eligible}) >= 2,
                    'Long-work coverage missing: ' + name + '/' + label)
        # A frozen unit retains source character coordinates, preventing adjacent reuse.
        by_source = {}
        for row in rows[name]:
            start, end = row['source_char_span']
            require(0 <= start < end, 'Invalid source span')
            by_source.setdefault(row['source_id'], []).append((start, end))
        for spans in by_source.values():
            ordered = sorted(spans)
            require(all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:])), 'Overlapping references')
    return freeze, rows


def preflight(require_freeze=True):
    p = protocol_check()
    report = {'protocol_and_environment': 'passed', 'training_executed': False,
              'S_opened': False, 'core_sha256': filehash(Path(core.__file__)),
              'legacy_runner_sha256': filehash(ROOT / 'scripts/run_beto_first_training_v2.py')}
    if require_freeze:
        freeze, rows = frozen_inputs()
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(BASE, revision=REV, local_files_only=True)
        report['tokenization'] = {}
        for name, group in rows.items():
            lengths = [len(tok(r['text'], truncation=False)['input_ids']) for r in group]
            report['tokenization'][name] = dict(n=len(group), truncated=sum(n > 384 for n in lengths),
                                               maximum=max(lengths))
        report['freeze_sha256'] = filehash(FREEZE)
        report['C_ready'] = True
    else:
        report['C_ready'] = False
        report['limitation'] = 'Environment/core only; frozen references not admitted or loaded'
    return p, report


def by_work(rows, pred):
    return {family: metrics([r for r in rows if r['family_id'] == family],
                           [p for r, p in zip(rows, pred) if r['family_id'] == family])
            for family in sorted({r['family_id'] for r in rows})}


def baseline(train, val, dest, identity):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from threadpoolctl import threadpool_limits
    path = dest / 'baselines.json'
    if path.exists():
        old = read(path)
        require(old['identity'] == identity, 'Baseline identity differs')
        require(metrics(val, old['predictions']) == old['tfidf'], 'Baseline metrics differ')
        return old
    started = time.perf_counter()
    majority = sorted(Counter(r['label'] for r in train).items(), key=lambda x: (-x[1], x[0]))[0][0]
    model = make_pipeline(TfidfVectorizer(strip_accents='unicode', ngram_range=(1, 2), min_df=2,
                                         max_features=50000, sublinear_tf=True),
                          LogisticRegression(C=4., class_weight='balanced', max_iter=2000,
                                             random_state=42, solver='lbfgs'))
    with threadpool_limits(limits=1):
        model.fit([r['text'] for r in train], [r['label'] for r in train])
        pred = model.predict([r['text'] for r in val]).tolist()
    result = dict(identity=identity, tfidf=metrics(val, pred), by_work=by_work(val, pred),
                  majority=metrics(val, [majority] * len(val)), predictions=pred,
                  seconds=time.perf_counter() - started)
    save(path, result)
    return result


def spent():
    attempts = [read(p) for p in (OUT / 'attempts').glob('*.json')]
    # Unsettled attempts reserve their full allowance after process/power failure.
    return sum(a.get('wall_seconds', a['reserved_seconds']) for a in attempts)


def report_results():
    _, rows = frozen_inputs()
    result_rows = []
    attempts = [read(p) for p in (OUT / 'attempts').glob('*.json')]
    require(all('wall_seconds' in a for a in attempts), 'Unsettled compute attempt; report cannot hide unknown time')
    for name in EXPECTED:
        dest = OUT / 'seed-42' / name
        config = read(dest / 'config.json')
        require(config['execution']['freeze_sha256'] == filehash(FREEZE), 'Result uses other freeze')
        result = verify_result(dest, config, rows['V'])
        baseline_path = OUT / 'baselines' / ('H' if name == 'R0' else 'H-T300') / 'baselines.json'
        base = read(baseline_path)
        require(base['identity']['V'] == fingerprint(rows['V']), 'Baseline uses other V')
        result_rows.append(dict(recipe=name, seed=42, epochs=len(result['history']), best_epoch=result['best_epoch'],
                                metrics=result['metrics']['combined'], by_work=read(dest / 'by-work.json'),
                                tfidf_metrics=base['tfidf'], tfidf_seconds=base['seconds'],
                                successful_core_seconds=result['seconds'],
                                cumulative_attempt_wall_seconds=sum(a['wall_seconds'] for a in attempts if a['recipe'] == name),
                                checkpoint=str((dest / f"checkpoint-{result['best_epoch']}").relative_to(ROOT)),
                                result_sha256=filehash(dest / 'result.json')))
    best = max(r['metrics']['f1_macro'] for r in result_rows[1:])
    tied = [r for r in result_rows[1:] if best - r['metrics']['f1_macro'] < .005]
    candidate = min(tied, key=lambda r: (r['cumulative_attempt_wall_seconds'], r['recipe']))['recipe']
    summary = dict(freeze_sha256=filehash(FREEZE), seed=42, S_opened=False,
                   primary='pooled V macro F1, seven explicit classes', candidate=candidate,
                   compute_seconds_all_attempts=spent(), results=result_rows)
    core.persist(OUT / 'comparison-seed42.json', summary)
    lines = ['| Receta | F1 macro V | TF-IDF | Mejor época | Segundos acumulados | Checkpoint |',
             '|---|---:|---:|---:|---:|---|']
    for row in result_rows:
        lines.append(f"| {row['recipe']} | {row['metrics']['f1_macro']:.6f} | {row['tfidf_metrics']['f1_macro']:.6f} | {row['best_epoch']} | {row['cumulative_attempt_wall_seconds']:.2f} | {row['checkpoint']} |")
    print('\n'.join(lines))
    return summary


def run(recipe, seed=42):
    entry_started = time.perf_counter()
    require(seed in (42, 43, 44), 'Unapproved seed')
    require(seed == 42 or recipe in ('R0', 'R2'), 'D permits only R0/R2')
    p, report = preflight()
    freeze, rows = frozen_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    lock = OUT / 'run.lock'
    with lock.open('x') as handle:
        handle.write('Single GPU owner; an abandoned lock requires checking no active run.\n')
    try:
        names = EXPECTED if recipe == 'all' else [recipe]
        for name in names:
            data, lr, epochs = EXPECTED[name]
            train = [r for group in data for r in rows[group]]
            val = rows['V']
            config = {**p, 'execution': dict(seed=seed, recipe=name, lr=lr, epochs=epochs,
                       train_rows_hash=fingerprint(train), validation_rows_hash=fingerprint(val),
                       freeze_sha256=filehash(FREEZE), core_sha256=report['core_sha256'],
                       legacy_runner_sha256=report['legacy_runner_sha256'],
                       runner_sha256=filehash(__file__))}
            if seed != 42:
                config['execution']['retention'] = 'best_and_latest'
            dest = OUT / f'seed-{seed}' / name
            core.persist(dest / 'config.json', config)
            base = baseline(train, val, OUT / 'baselines' / ('H' if name == 'R0' else 'H-T300'),
                            dict(train=fingerprint(train), V=fingerprint(val), protocol=filehash(ART / 'protocol.json')))
            if not (dest / 'result.json').exists():
                # Freeze pins the cumulative ledger BEFORE any phase C attempt.
                prior = read(pinned(freeze['budget_ledger']))
                allowance = min(p['budget']['CD_gpu_seconds'] - prior['CD_training_gpu_seconds'],
                                p['budget']['total_training_gpu_seconds'] - prior['new_training_gpu_seconds']) - spent()
                require(allowance > 180, 'Insufficient remaining compute allowance')
                require(shutil.disk_usage(OUT).free >= 4 * 1024**3, 'Less than 4 GiB free for safe checkpoint writes')
                trajectories = len(list(OUT.glob('seed-*/*/attempt-started.json')))
                marker = dest / 'attempt-started.json'
                if marker.exists() and not list(dest.glob('resume-epoch-*.pt')):
                    raise ValueError('Prior attempt has no resumable epoch; reconcile failed trajectory before restarting')
                if not marker.exists():
                    require(trajectories < (4 if seed == 42 else 8) and prior['new_training_trajectories'] + trajectories < 18,
                            'Trajectory ceiling reached')
                    save(marker, dict(recipe=name, config_hash=fingerprint(config)))
                attempt = dict(recipe=name, seed=seed, started_utc=datetime.now(timezone.utc).isoformat(),
                               status='reserved', reserved_seconds=allowance,
                               config_hash=fingerprint(config))
                path = OUT / 'attempts' / (str(uuid.uuid4()) + '.json')
                save(path, attempt)
                started = entry_started if seed != 42 else time.perf_counter()
                def check():
                    require(time.perf_counter() - started < allowance - 120, 'Compute budget stop (saving margin)')
                core._BUDGET_CHECK = check
                try:
                    core.train_run(train, val, dest, config)
                    attempt['status'] = 'complete'
                except BaseException as exc:
                    attempt['status'] = 'failed_or_interrupted'
                    attempt['error'] = repr(exc)
                    raise
                finally:
                    attempt['wall_seconds'] = time.perf_counter() - started
                    temporary = path.with_suffix('.tmp')
                    temporary.write_text(json.dumps(attempt, indent=2), encoding='utf-8')
                    temporary.replace(path)
                    core._BUDGET_CHECK = lambda: None
            result = verify_result(dest, config, val)
            require(len(result['history']) == epochs, 'Incomplete epoch history')
            require(result['best_epoch'] == max(result['history'], key=lambda h: h['f1_macro'])['epoch'],
                    'Wrong best epoch or tie break')
            core.persist(dest / 'by-work.json', by_work(val, [r['predicted'] for r in result['predictions']]))
            print(json.dumps(dict(recipe=name, f1=result['metrics']['combined']['f1_macro'],
                                  tfidf=base['tfidf']['f1_macro'], checkpoint=str(dest / f"checkpoint-{result['best_epoch']}"))))
    finally:
        lock.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['preflight', 'environment', 'run', 'report'])
    parser.add_argument('--recipe', choices=['all', *EXPECTED], default='all')
    parser.add_argument('--seed', type=int, choices=[42, 43, 44], default=42)
    args = parser.parse_args()
    try:
        if args.command == 'run':
            run(args.recipe, args.seed)
        elif args.command == 'report':
            report_results()
        else:
            print(json.dumps(preflight(args.command == 'preflight')[1], indent=2))
    except (ValueError, FileNotFoundError) as exc:
        print('BLOCKED: ' + str(exc))
        raise SystemExit(2)
