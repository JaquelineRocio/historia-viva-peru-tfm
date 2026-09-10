"""Diagnose saved BETO checkpoints on their training rows, with no fitting."""
from __future__ import annotations

import importlib.metadata
import time
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from compare_beto_length import ROOT, metric_report, read, sha, write
from verify_external_development import fingerprint, workspace_file

ARTIFACTS = ROOT / 'artifacts/experiments/beto-training-fit-v1'
OUTPUT = ROOT / 'outputs/beto-training-fit-v1'
ARMS = {
    'reference': ('artifacts/experiments/beto-length-v1', 'outputs/beto-length-v1/run/candidate', 596),
    'candidate': ('artifacts/experiments/beto-data-v3', 'outputs/beto-data-v3/run/candidate', 619),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def train_rows(payload):
    # No old evaluation text/label reaches the model or semantic diagnostic.
    return [(i, row) for i, row in enumerate(payload['items']) if row['split'] == 'train']


def identity(row):
    return row['resourceId'], row['text'], row['label']


def common_indices(before, after):
    """Pair a multiset, consuming each duplicate occurrence at most once."""
    positions = defaultdict(deque)
    for i, (_, row) in enumerate(after):
        positions[identity(row)].append(i)
    return [(i, positions[identity(row)].popleft()) for i, (_, row) in enumerate(before)
            if positions[identity(row)]]


def summarize(rows, predictions, labels):
    require(len(rows) == len(predictions) and bool(rows), 'Aligned nonempty predictions required')
    present = [label for label in labels if any(row['label'] == label for row in rows)]
    result = metric_report([row['label'] for row in rows], predictions, labels, present)
    result['per_source'] = {}
    for source in sorted({row['resourceId'] for row in rows}):
        indices = [i for i, row in enumerate(rows) if row['resourceId'] == source]
        truth = [rows[i]['label'] for i in indices]
        result['per_source'][source] = metric_report(
            truth, [predictions[i] for i in indices], labels, [label for label in labels if label in truth])
    return result


def evidence(relative):
    return dict(path=relative, sha256=sha(workspace_file(relative)))


def prepare():
    train, parents, guards, saved = {}, {}, {}, {}
    for arm, (folder, directory, count) in ARMS.items():
        protocol_path, report_path = folder + '/protocol.json', folder + '/report.json'
        parent, report = read(workspace_file(protocol_path)), read(workspace_file(report_path))
        require(report['protocol']['sha256'] == sha(workspace_file(protocol_path)), 'Parent protocol/report link differs')
        parent_body = {k: v for k, v in parent.items() if k != 'content_sha256'}
        require(parent['content_sha256'] == fingerprint(parent_body), 'Parent protocol content differs')
        path = parent['training_dataset']
        payload = read(workspace_file(path))
        expected_sha = next(e['sha256'] for e in parent['input_guards'] if e['path'] == path)
        require(sha(workspace_file(path)) == expected_sha, 'Training snapshot changed')
        train[arm] = train_rows(payload)
        require(len(train[arm]) == count and fingerprint([row for _, row in train[arm]]) == parent['training_rows_sha256'],
                'Training membership/order differs from checkpoint recipe')
        require(payload['labels'] == parent['labels'], 'Dataset taxonomy differs')
        del payload
        mapping = {str(i): label for i, label in enumerate(parent['labels'])}
        require(read(workspace_file(directory + '/labels.json')) == {'id2label': mapping, 'max_len': 384}, 'Labels/max_len differ')
        config = read(workspace_file(directory + '/config.json'))
        require(config['id2label'] == mapping and config['label2id'] == {label: int(i) for i, label in mapping.items()},
                'Model label map differs')
        for entry in report['candidate_files']:
            require(str(Path(entry['path']).parent).replace('\\', '/') == directory, 'Wrong checkpoint directory')
            require(sha(workspace_file(entry['path'])) == entry['sha256'], 'Checkpoint bytes changed')
            guards[entry['path']] = evidence(entry['path'])
        for name in [protocol_path, report_path, path]:
            guards[name] = evidence(name)
        require(report['training_details']['max_len'] == 384 and report['training_details']['checkpoint_epoch'] == 2,
                'Only saved epoch2/384 checkpoints are supported')
        parents[arm] = parent
        saved[arm] = dict(external_metrics=report['after'], external_per_item=report['per_item'])
    require(parents['reference']['labels'] == parents['candidate']['labels'], 'Checkpoint taxonomies differ')
    require(parents['reference']['external_content_sha256'] == parents['candidate']['external_content_sha256'],
            'Saved external sets differ')
    a, b = saved['reference']['external_per_item'], saved['candidate']['external_per_item']
    require(len(a) == len(b) == 31 and all(
        (x['id'], x['source'], x['truth'], x['text_sha256'], x['after']) ==
        (y['id'], y['source'], y['truth'], y['text_sha256'], y['before']) for x, y in zip(a, b)),
        'Saved external prediction chain differs')
    for name in ['tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt']:
        require(sha(workspace_file(ARMS['reference'][1] + '/' + name)) ==
                sha(workspace_file(ARMS['candidate'][1] + '/' + name)), 'Checkpoint tokenizers differ')
    pairs = common_indices(train['reference'], train['candidate'])
    require(len(pairs) == 560, 'Shared training membership differs')
    application_path = 'artifacts/experiments/beto-data-v3/application.json'
    application = read(workspace_file(application_path))
    new_sources = set(application['new_source_ids'].values())
    additions = [i for i, (_, row) in enumerate(train['candidate']) if row['resourceId'] in new_sources]
    require(len(new_sources) == 5 and len(additions) == 30, 'New training works/rows differ')
    common_candidate = {j for _, j in pairs}
    require(not common_candidate.intersection(additions), 'New additions intersect shared rows')
    changed = [i for i in range(619) if i not in common_candidate and i not in additions]
    require(len(changed) == 29, 'Changed preexisting-source rows differ')
    for name in [application_path, 'scripts/diagnose_beto_training_fit.py', 'scripts/compare_beto_length.py',
                 'scripts/verify_external_development.py', 'apps/ml/app/ml/beto_experiment.py',
                 'apps/ml/app/ml/baselines.py']:
        guards[name] = evidence(name)
    for package, version in parents['candidate']['packages'].items():
        require(importlib.metadata.version(package) == version, 'Changed package: ' + package)
    protocol = dict(
        schema_version=1, id='beto-training-fit-v1', status='frozen_before_training_predictions',
        declared_at_utc=datetime.now(timezone.utc).isoformat(),
        question='¿Las categorías con cero aciertos externos también fallan en los ejemplos usados para aprender?',
        inference_params=dict(batch_size=2, max_len=384), labels=parents['candidate']['labels'],
        arms={arm: dict(training_dataset=parents[arm]['training_dataset'],
                       training_rows_sha256=parents[arm]['training_rows_sha256'], rows=ARMS[arm][2],
                       checkpoint_directory=ARMS[arm][1], checkpoint_epoch=2) for arm in ARMS},
        paired_common_rows=560,
        paired_common_unique_identities=len({identity(train['reference'][i][1]) for i, _ in pairs}),
        common_pair_indices_sha256=fingerprint(pairs),
        candidate_addition_indices=additions, candidate_changed_existing_source_indices=changed,
        comparison='Own-training metrics are in-sample and use different sets596/619. Compare both checkpoints only on the identical560-row multiset; retain duplicate occurrences and disclose them.',
        metrics='Global and per-source confusion matrices and precision/recall/F1/support. Macro uses the exact truth-supported labels named in each report. No direct aggregate comparison to external five-label macro.',
        interpretation_rule='Observe counts/recalls before proposing causes. Train successes with external failures establish a descriptive transfer gap; train failures establish incomplete fit too. Neither uniquely identifies a cause. No performance threshold, model selection or new fitting.',
        external_policy='Reuse the two saved external reports without loading the external dataset or running new inference on it. Original val/test receive no inference or semantic analysis.',
        packages=parents['candidate']['packages'], input_guards=list(guards.values()),
        limits=['Training accuracy can be optimistic from memorization/source cues; not a quality estimate for new sources.',
                'Two fixed checkpoints, one seed and mixed historical data changes; no single causal conclusion.',
                'Annotations include AI-assisted review, not independent human gold. Do not relabel from predictions.',
                'Shared training has a preexisting duplicate; occurrences are paired one-to-one, not multiplied.',
                'External31 was reused and covers five classes in two related works; independent final evaluation remains pending.',
                'No training, checkpoint selection, source change, test prediction, paid service or production operation.'],
        training_performed=False, production_changed=False)
    protocol['content_sha256'] = fingerprint(protocol)
    return protocol, train, pairs, saved


def run():
    require(not OUTPUT.exists() and not ARTIFACTS.exists(), 'Diagnostic output already exists; no overwrite/repeat')
    protocol, train, pairs, saved = prepare()
    import torch
    from app.ml.beto_experiment import predict_beto
    require(torch.cuda.is_available(), 'CUDA required; no automatic CPU fallback')
    torch.set_num_threads(4)
    ARTIFACTS.mkdir(parents=True, exist_ok=False)
    protocol_path = ARTIFACTS / 'protocol.json'
    write(protocol_path, protocol)
    protocol_hash = sha(protocol_path)
    OUTPUT.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    predictions, arms = {}, {}
    stage = 'training_row_inference'
    try:
        for arm, (_, directory, _) in ARMS.items():
            rows = [row for _, row in train[arm]]
            print(f'Inferring {arm}: {len(rows)} TRAIN rows; no fitting', flush=True)
            predictions[arm] = predict_beto(workspace_file(directory + '/config.json').parent,
                                             rows, protocol['labels'], protocol['inference_params'])
            require(len(predictions[arm]) == len(rows), 'Prediction count differs')
            records = [dict(train_index=i, snapshot_index=index, source=row['resourceId'], truth=row['label'],
                            text_sha256=sha256(row['text'].encode('utf-8')).hexdigest(),
                            predicted=predictions[arm][i], correct=predictions[arm][i] == row['label'])
                       for i, (index, row) in enumerate(train[arm])]
            write(OUTPUT / (arm + '-train-predictions.json'), dict(items=records))
            arms[arm] = dict(own_train=summarize(rows, predictions[arm], protocol['labels']),
                             saved_external=saved[arm]['external_metrics'])
        common, paired = {}, []
        for arm, position in [('reference', 0), ('candidate', 1)]:
            indices = [pair[position] for pair in pairs]
            common[arm] = summarize([train[arm][i][1] for i in indices],
                                    [predictions[arm][i] for i in indices], protocol['labels'])
        for i, j in pairs:
            row = train['reference'][i][1]
            paired.append(dict(reference_train_index=i, candidate_train_index=j,
                               truth=row['label'], source=row['resourceId'],
                               before=predictions['reference'][i], after=predictions['candidate'][j]))
        subset_metrics = {}
        for name, indices in [('additions30', protocol['candidate_addition_indices']),
                              ('changed_existing_sources29', protocol['candidate_changed_existing_source_indices'])]:
            subset_metrics[name] = summarize([train['candidate'][i][1] for i in indices],
                                             [predictions['candidate'][i] for i in indices], protocol['labels'])
        stage = 'final_integrity'
        require(sha(protocol_path) == protocol_hash, 'Protocol changed during inference')
        for entry in protocol['input_guards']:
            require(sha(workspace_file(entry['path'])) == entry['sha256'], 'Input changed during inference: ' + entry['path'])
        report = dict(schema_version=1, purpose='in_sample_training_fit_diagnostic',
                      created_at_utc=datetime.now(timezone.utc).isoformat(),
                      protocol=dict(path=protocol_path.relative_to(ROOT).as_posix(), sha256=protocol_hash,
                                    content_sha256=protocol['content_sha256']),
                      arms=arms, common560=common, common_pairs=paired, candidate_subsets=subset_metrics,
                      prediction_files=[evidence((OUTPUT / (arm + '-train-predictions.json')).relative_to(ROOT).as_posix()) for arm in ARMS],
                      new_inference_rows=1215, model_loads=2, training_performed=False,
                      old_validation_predictions_performed=False, test_predictions_performed=False,
                      external_predictions_reused=True, new_external_predictions_performed=False,
                      production_changed=False, inputs_unchanged=True, offline=True,
                      seconds=round(time.perf_counter() - started, 2), cuda_device=torch.cuda.get_device_name(),
                      limits=protocol['limits'])
        write(OUTPUT / 'report.json', report)
        print({arm: {'train_correct': value['own_train']['correct'], 'f1': value['own_train']['f1_macro']}
               for arm, value in arms.items()}, flush=True)
        return report
    except Exception as exc:
        write(OUTPUT / 'failure.json', dict(stage=stage, error_type=type(exc).__name__, message=str(exc),
                                           training_performed=False, automatic_retry=False, production_changed=False))
        raise


if __name__ == '__main__':
    run()
