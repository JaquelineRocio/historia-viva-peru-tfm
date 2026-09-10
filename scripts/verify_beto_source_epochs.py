"""Independently recalculate stored source/epoch results; no model imports."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, f1_score

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'artifacts/experiments/beto-source-epochs-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def main():
    output = FOLDER / 'verification.json'
    if output.exists():
        raise ValueError('Verification already exists; no overwrite')
    protocol, report = read(FOLDER / 'protocol.json'), read(FOLDER / 'report.json')
    assert protocol['content_sha256'] == fingerprint({k: v for k, v in protocol.items() if k != 'content_sha256'})
    assert report['protocol']['sha256'] == digest(FOLDER / 'protocol.json')
    assert read(ROOT / 'outputs/beto-source-epochs-v1/report.json') == report
    checked_paths = set()
    for entry in protocol['input_guards'] + report['checkpoint_files'] + report['prediction_files']:
        path = (ROOT / entry['path']).resolve()
        assert path.is_relative_to(ROOT) and path.is_file()
        assert digest(path) == entry['sha256'], entry['path']
        checked_paths.add(entry['path'])
    data = read(ROOT / protocol['dataset'])
    indexed = [(i, row) for i, row in enumerate(data['items']) if row['split'] == 'train']
    rows = [row for _, row in indexed]
    labels = protocol['labels']
    assert len(rows) == 619 and fingerprint(rows) == protocol['training_rows_sha256']
    # Evaluation handled only as a byte-equivalent object, never as semantic input.
    original = read(ROOT / 'artifacts/datasets/gold-v1-source-aware.json')
    assert [r for r in original['items'] if r['split'] != 'train'] == [r for r in data['items'] if r['split'] != 'train']
    del data, original
    metric_count = 0

    def verify_metrics(indices, records, saved):
        nonlocal metric_count
        truth = [rows[i]['label'] for i in indices]
        pred = [records[i]['predicted'] for i in indices]
        present = [label for label in labels if label in truth]
        assert saved['labels'] == labels and saved['metric_labels'] == present
        assert saved['rows'] == len(indices) and saved['correct'] == sum(a == b for a, b in zip(truth, pred))
        assert math.isclose(saved['accuracy'], saved['correct'] / len(indices), abs_tol=1e-12)
        assert saved['confusion_matrix'] == confusion_matrix(truth, pred, labels=labels).tolist()
        assert math.isclose(saved['f1_macro'], f1_score(truth, pred, labels=present, average='macro', zero_division=0), abs_tol=1e-12)
        p, r, f, s = precision_recall_fscore_support(truth, pred, labels=labels, zero_division=0)
        for i, c in enumerate(saved['per_class']):
            assert c['label'] == labels[i] and c['support'] == s[i] and c['predicted_count'] == pred.count(labels[i])
            assert all(math.isclose(c[k], v, abs_tol=1e-12) for k, v in [('precision', p[i]), ('recall', r[i]), ('f1', f[i])])
        assert saved['predictions_to_unassessed_labels'] == {label: pred.count(label) for label in labels if label not in present}
        metric_count += 1

    deltas, summaries = {}, {}
    seen_prediction_paths = set()
    for fold in protocol['folds']:
        name = fold['id']
        fit = [i for i, r in enumerate(rows) if r['resourceId'] not in fold['held_sources']]
        held = [i for i, r in enumerate(rows) if r['resourceId'] in fold['held_sources']]
        primary = [i for i, r in enumerate(rows) if r['resourceId'] == fold['primary_source']]
        assert fit == fold['fit_indices'] and held == fold['held_indices'] and primary == fold['primary_indices']
        assert set(fit).isdisjoint(held) and sorted(fit + held) == list(range(619))
        assert {rows[i]['label'] for i in fit} == set(labels)
        assert fingerprint([rows[i] for i in fit]) == fold['fit_sha256']
        assert fingerprint([rows[i] for i in held]) == fold['held_sha256']
        details = report['folds'][name]['training_details']
        assert details == read(ROOT / 'outputs/beto-source-epochs-v1' / name / 'training-details.json')
        counts = Counter(rows[i]['label'] for i in fit)
        assert details['class_counts'] == dict(counts) == fold['fit_class_counts']
        for label in labels:
            weight = len(fit) / (len(labels) * counts[label])
            assert math.isclose(details['class_weights'][label], weight, rel_tol=1e-6)
            assert math.isclose(fold['class_weights'][label], weight, rel_tol=1e-12)
        microbatches = math.ceil(len(fit) / 2)
        steps = math.ceil(microbatches / 8)
        total, warmup = steps * 3, max(1, int(steps * 3 * .1))
        assert details['schedule_total_steps'] == total and details['warmup_steps'] == warmup
        assert len(details['history']) == 3 and details['checkpoint_epochs'] == [2, 3]
        updates = skips = 0
        for epoch, record in enumerate(details['history'], 1):
            assert record['epoch'] == epoch and record['microbatches'] == microbatches
            assert record['optimizer_updates'] + record['skipped_updates'] == steps
            updates += record['optimizer_updates']
            skips += record['skipped_updates']
            lr = 2e-5 * min((updates + 1) / warmup, max(0., (total - updates) / (total - warmup)))
            assert math.isclose(record['learning_rate_after_epoch'], lr, abs_tol=1e-14)
            if epoch in [2, 3]:
                saved = next(s for s in details['saved_checkpoints'] if s['epoch'] == epoch)
                assert saved['optimizer_updates'] == saved['scheduler_steps'] == updates
                assert saved['skipped_updates'] == skips and saved['optimizer_update_attempts'] == epoch * steps
        assert details['optimizer_updates'] == updates and details['skipped_updates'] == skips
        assert details['optimizer_update_attempts'] == total and details['scheduler_steps'] == updates
        all_predictions, per_epoch = {}, {}
        for epoch in [2, 3]:
            directory = ROOT / 'outputs/beto-source-epochs-v1' / name / f'epoch-{epoch}'
            mapping = {str(i): label for i, label in enumerate(labels)}
            cfg = read(directory / 'config.json')
            assert cfg['id2label'] == mapping and cfg['label2id'] == {v: int(k) for k, v in mapping.items()}
            assert read(directory / 'labels.json') == dict(id2label=mapping, max_len=384)
            for token in ['tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt']:
                assert digest(directory / token) == digest(ROOT / 'outputs/beto-data-v3/run/candidate' / token)
            path = directory.parent / f'epoch-{epoch}-predictions.json'
            seen_prediction_paths.add(path.relative_to(ROOT).as_posix())
            records = read(path)['items']
            assert len(records) == 619
            for i, p in enumerate(records):
                snapshot_index, row = indexed[i]
                assert p['train_index'] == i and p['snapshot_index'] == snapshot_index
                assert (p['source'], p['truth']) == (row['resourceId'], row['label'])
                assert p['text_sha256'] == hashlib.sha256(row['text'].encode('utf-8')).hexdigest()
                assert p['predicted'] in labels and p['role'] == ('fit' if i in fit else 'held')
            saved = report['folds'][name]['epochs'][str(epoch)]
            all_predictions[epoch] = records
            per_epoch[epoch] = {}
            for subset, indices in [('fit', fit), ('held', held), ('primary', primary)]:
                verify_metrics(indices, records, saved[subset])
                ideas = [i for i in indices if rows[i]['label'] == 'crisis_ideas_emancipadoras']
                per_epoch[epoch][subset] = dict(ideas_correct=sum(records[i]['predicted'] == rows[i]['label'] for i in ideas),
                    ideas_support=len(ideas), correct=saved[subset]['correct'], rows=len(indices), f1_macro=saved[subset]['f1_macro'])
            for source in sorted({r['resourceId'] for r in rows}):
                verify_metrics([i for i, r in enumerate(rows) if r['resourceId'] == source], records, saved['per_source'][source])
        deltas[name] = {subset: per_epoch[3][subset]['ideas_correct'] - per_epoch[2][subset]['ideas_correct'] for subset in ['fit', 'primary']}
        paired = {}
        for subset, indices in [('fit', fit), ('primary', primary), ('held', held)]:
            corrected = introduced = changed = 0
            for i in indices:
                a, b, truth = all_predictions[2][i]['predicted'], all_predictions[3][i]['predicted'], rows[i]['label']
                corrected += a != truth and b == truth
                introduced += a == truth and b != truth
                changed += a != b
            paired[subset] = dict(corrected_errors=corrected, introduced_errors=introduced, changed_predictions=changed)
        summaries[name] = dict(epochs=per_epoch, paired=paired, updates=updates, skips=skips)
    assert seen_prediction_paths == {e['path'] for e in report['prediction_files']}
    assert len(report['checkpoint_files']) == 28 and len(report['prediction_files']) == 4
    expected = ('exploratory_signal_of_additional_learning_and_transfer' if all(x['fit'] > 0 and x['primary'] > 0 for x in deltas.values())
                else 'transfer_difficulty_persists' if all(x['fit'] > 0 and x['primary'] <= 0 for x in deltas.values())
                else 'inconclusive_or_work_dependent')
    assert report['decision']['status'] == expected and report['decision']['ideas_correct_deltas'] == deltas
    assert report['decision']['selected_model'] is None and report['decision']['selected_epoch'] is None
    assert all(report[key] is False for key in ['old_validation_predictions_performed', 'test_predictions_performed',
                                               'external_predictions_performed', 'labels_changed', 'production_changed'])
    result = dict(status='passed', created_at_utc=datetime.now(timezone.utc).isoformat(),
                  report_sha256=digest(FOLDER / 'report.json'), verifier_sha256=digest(Path(__file__)),
                  guarded_files_verified=len(checked_paths), metric_summaries_recomputed=metric_count,
                  prediction_rows_verified=2476, unchanged_original_evaluation_rows=218,
                  summaries=summaries, decision=expected, models_loaded=False, training_performed=False,
                  limits='Recalculation of saved predictions verifies metrics and integrity, not historical correctness or independent generalization.')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
