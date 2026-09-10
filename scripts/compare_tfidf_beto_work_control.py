"""Frozen two-fit TF-IDF control using existing BETO TRAIN partitions/predictions."""
from __future__ import annotations

import argparse
import importlib.metadata
import sys
import time
import warnings
from collections import Counter
from hashlib import sha256

from compare_beto_source_epochs import ROOT, DATASET, IDEAS, make_folds, now, train_only
from compare_beto_length import metric_report, read, sha, write
from verify_external_development import fingerprint

sys.path.insert(0, str(ROOT / 'apps/ml'))
ART = ROOT / 'artifacts/experiments/tfidf-beto-work-control-v1'
OUT = ROOT / 'outputs/tfidf-beto-work-control-v1'
PARENT = 'artifacts/experiments/beto-source-epochs-v1/protocol.json'


def guard(path):
    return dict(path=path, sha256=sha(ROOT / path))


def freeze():
    assert not ART.exists() and not OUT.exists(), 'No overwrite or repeated experiment'
    parent = read(ROOT / PARENT)
    assert fingerprint({k: v for k, v in parent.items() if k != 'content_sha256'}) == parent['content_sha256']
    data = read(ROOT / DATASET)
    rows = [r for _, r in train_only(data)]
    assert len(rows) == 619 and fingerprint(rows) == parent['training_rows_sha256']
    assert make_folds(rows, parent['labels']) == parent['folds']
    config = read(ROOT / 'configs/experiments/tfidf.json')
    selection = read(ROOT / 'outputs/history-comparison-v1/reviewed/selection.json')
    params = next(p for p in config['trials'] if p['id'] == selection['selected'])
    assert params == dict(id='tfidf-c4', C=4.0) and config['seed'] == 42
    paths = [PARENT, DATASET, 'configs/experiments/tfidf.json',
             'outputs/history-comparison-v1/reviewed/selection.json',
             'apps/ml/app/ml/experiments.py', 'scripts/compare_beto_length.py',
             'scripts/compare_beto_source_epochs.py', 'scripts/verify_external_development.py',
             'scripts/compare_tfidf_beto_work_control.py', 'scripts/compare_beto_validation.py',
             'docs/guia-etiquetado-1780-1842.md',
             'artifacts/reviews/beto-historiography-boundary-v1.json']
    paths += [f"outputs/beto-source-epochs-v1/{f['id']}/epoch-{e}-predictions.json"
              for f in parent['folds'] for e in (2, 3)]
    # Preserve inherited evidence without inspecting external texts or evaluating them.
    guards = {g['path']: g for g in parent['input_guards']}
    for g in guards.values():
        assert sha(ROOT / g['path']) == g['sha256'], g['path']
    guards.update({p: guard(p) for p in paths})
    protocol = dict(status='frozen_before_training', created_at_utc=now(),
        dataset=DATASET, labels=parent['labels'], folds=parent['folds'], params=params,
        seed=42, thread_limit=1, training_rows_sha256=fingerprint(rows),
        evaluation_sha256=fingerprint([r for r in data['items'] if r['split'] != 'train']),
        input_guards=list(guards.values()),
        packages={p: importlib.metadata.version(p) for p in
                  ('scikit-learn', 'numpy', 'scipy', 'joblib', 'threadpoolctl')},
        comparison='Exactly two fresh word TF-IDF fits using existing fit_tfidf; full original texts, no corpus edits. BETO epoch2 primary; epoch3 secondary, no epoch selection.',
        outcomes='Per-work correct count, supported-label and seven-label macro F1, per-class confusion; paired corrections/new errors. Fit metrics descriptive. No pooled headline across works.',
        decision_rule='If TF-IDF improves ideas correct count AND supported-label macro F1 on BOTH primary works over epoch2: signal to investigate BETO recipe/representation. If both methods have zero ideas correct on BOTH works: shared transfer failure, prioritize independently reviewed cross-work data/evaluation before tuning. Otherwise: mixed/work-dependent, no winner.',
        limits='Exploratory reused TRAIN holdouts, not independent test or causal isolation. Text representations/input lengths differ. No significance, readiness or architecture-incapacity claim. No test/val/external predictions; no BETO training; no model promotion.',
        stopping_rule='Stop after two fits and verification; no additional variant or hyperparameter search.')
    protocol['content_sha256'] = fingerprint(protocol)
    ART.mkdir(parents=True)
    write(ART / 'protocol.json', protocol)
    print('Protocol frozen; no model fitted.', flush=True)


def inputs():
    p = read(ART / 'protocol.json')
    assert fingerprint({k: v for k, v in p.items() if k != 'content_sha256'}) == p['content_sha256']
    for g in p['input_guards']:
        assert sha(ROOT / g['path']) == g['sha256'], g['path']
    for k, v in p['packages'].items():
        assert importlib.metadata.version(k) == v
    data = read(ROOT / p['dataset'])
    indexed = train_only(data)
    rows = [r for _, r in indexed]
    assert fingerprint(rows) == p['training_rows_sha256']
    assert fingerprint([r for r in data['items'] if r['split'] != 'train']) == p['evaluation_sha256']
    assert make_folds(rows, p['labels']) == p['folds']
    return p, indexed, rows


def score(rows, predictions, indices, labels):
    truth = [rows[i]['label'] for i in indices]
    result = metric_report(truth, [predictions[i] for i in indices], labels,
                           [l for l in labels if l in truth])
    result['f1_macro_all_seven'] = sum(c['f1'] for c in result['per_class']) / len(labels)
    return result


def summaries(p, rows, fold, predictions):
    subsets = dict(fit=fold['fit_indices'], held=fold['held_indices'], primary=fold['primary_indices'])
    subsets.update({s: [i for i in fold['held_indices'] if rows[i]['resourceId'] == s]
                    for s in fold['held_sources'] if s != fold['primary_source']})
    return {name: {model: score(rows, pred, ix, p['labels']) for model, pred in predictions.items()}
            for name, ix in subsets.items()}


def beto_predictions(indexed, fold):
    result = {}
    for epoch in (2, 3):
        items = read(ROOT / f"outputs/beto-source-epochs-v1/{fold['id']}/epoch-{epoch}-predictions.json")['items']
        assert len(items) == len(indexed)
        for i, (item, (snapshot_index, row)) in enumerate(zip(items, indexed)):
            assert (item['train_index'], item['snapshot_index'], item['source'], item['truth'], item['text_sha256'], item['role']) == (
                i, snapshot_index, row['resourceId'], row['label'], sha256(row['text'].encode('utf-8')).hexdigest(),
                'fit' if i in fold['fit_indices'] else 'held')
        result[f'beto_epoch{epoch}'] = [r['predicted'] for r in items]
    return result


def run():
    import joblib
    from app.ml.experiments import fit_tfidf
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits
    p, indexed, rows = inputs()
    assert not OUT.exists() and not (ART / 'report.json').exists()
    OUT.mkdir(parents=True)
    report = dict(created_at_utc=now(), protocol=guard(str((ART / 'protocol.json').relative_to(ROOT)).replace('\\', '/')),
                  fits=2, beto_retrained=False, evaluation_predictions_performed=False, corpus_changed=False, folds=[])
    for fold in p['folds']:
        predictions = beto_predictions(indexed, fold)
        started = time.perf_counter()
        with threadpool_limits(limits=1), warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            model = fit_tfidf([rows[i] for i in fold['fit_indices']], p['params'], p['seed'])
            predictions['tfidf'] = model.predict([r['text'] for r in rows]).tolist()
        joblib.dump(model, OUT / (fold['id'] + '.joblib'))
        entries = [dict(train_index=i, snapshot_index=si, source=r['resourceId'], truth=r['label'],
                        text_sha256=sha256(r['text'].encode('utf-8')).hexdigest(),
                        role='fit' if i in fold['fit_indices'] else 'held',
                        **{name: pred[i] for name, pred in predictions.items()}) for i, (si, r) in enumerate(indexed)]
        write(OUT / (fold['id'] + '-predictions.json'), dict(items=entries))
        paired = {}
        for epoch in (2, 3):
            b, t = predictions[f'beto_epoch{epoch}'], predictions['tfidf']
            paired[str(epoch)] = dict(corrected=[indexed[i][0] for i in fold['primary_indices'] if t[i] == rows[i]['label'] != b[i]],
                new_errors=[indexed[i][0] for i in fold['primary_indices'] if b[i] == rows[i]['label'] != t[i]],
                shared_errors=[indexed[i][0] for i in fold['primary_indices'] if b[i] != rows[i]['label'] and t[i] != rows[i]['label']])
        report['folds'].append(dict(id=fold['id'], metrics=summaries(p, rows, fold, predictions), paired_primary=paired,
            vocabulary_size=len(model['tfidf'].vocabulary_), iterations=model['classifier'].n_iter_.tolist(),
            seconds=time.perf_counter()-started, fit_class_counts=dict(Counter(rows[i]['label'] for i in fold['fit_indices']))))
        print(f"Completed {fold['id']}", flush=True)
    def ideas(m):
        return next(c for c in m['per_class'] if c['label'] == IDEAS)['recall']
    primaries = [f['metrics']['primary'] for f in report['folds']]
    if all(ideas(m['tfidf']) > ideas(m['beto_epoch2']) and m['tfidf']['f1_macro'] > m['beto_epoch2']['f1_macro'] for m in primaries):
        decision = 'signal_to_investigate_beto_recipe_or_representation'
    elif all(ideas(m['tfidf']) == ideas(m['beto_epoch2']) == 0 for m in primaries):
        decision = 'shared_transfer_failure_prioritize_independent_data_and_evaluation'
    else:
        decision = 'mixed_or_work_dependent_no_winner'
    report['decision'] = decision
    report['output_guards'] = [guard(str(f.relative_to(ROOT)).replace('\\', '/')) for f in sorted(OUT.iterdir())]
    inputs()
    write(ART / 'report.json', report)
    print(decision)


def verify():
    from sklearn.metrics import confusion_matrix, f1_score
    p, indexed, rows = inputs()
    report = read(ART / 'report.json')
    assert report['protocol'] == guard(str((ART / 'protocol.json').relative_to(ROOT)).replace('\\', '/'))
    for g in report['output_guards']:
        assert sha(ROOT / g['path']) == g['sha256']
    checked = 0
    for fold, result in zip(p['folds'], report['folds']):
        assert fold['id'] == result['id']
        entries = read(OUT / (fold['id'] + '-predictions.json'))['items']
        prior = beto_predictions(indexed, fold)
        assert len(entries) == len(rows)
        for i, (entry, (si, row)) in enumerate(zip(entries, indexed)):
            assert (entry['train_index'], entry['snapshot_index'], entry['source'], entry['truth'], entry['text_sha256'], entry['role']) == (i, si, row['resourceId'], row['label'], sha256(row['text'].encode('utf-8')).hexdigest(), 'fit' if i in fold['fit_indices'] else 'held')
            assert entry['tfidf'] in p['labels']
            assert all(entry[k] == v[i] for k, v in prior.items())
        subsets = dict(fit=fold['fit_indices'], held=fold['held_indices'], primary=fold['primary_indices'])
        subsets.update({s: [i for i in fold['held_indices'] if rows[i]['resourceId'] == s] for s in fold['held_sources'] if s != fold['primary_source']})
        for subset, ix in subsets.items():
            truth = [rows[i]['label'] for i in ix]
            for model, m in result['metrics'][subset].items():
                pred = [entries[i][model] for i in ix]
                assert confusion_matrix(truth, pred, labels=p['labels']).tolist() == m['confusion_matrix']
                assert sum(a == b for a, b in zip(truth, pred)) == m['correct']
                for key, labels in [('f1_macro', m['metric_labels']), ('f1_macro_all_seven', p['labels'])]:
                    assert abs(f1_score(truth, pred, labels=labels, average='macro', zero_division=0)-m[key]) < 1e-12
                checked += 1
        for epoch in (2, 3):
            b = f'beto_epoch{epoch}'
            expected = dict(corrected=[indexed[i][0] for i in fold['primary_indices'] if entries[i]['tfidf'] == rows[i]['label'] != entries[i][b]],
                new_errors=[indexed[i][0] for i in fold['primary_indices'] if entries[i][b] == rows[i]['label'] != entries[i]['tfidf']],
                shared_errors=[indexed[i][0] for i in fold['primary_indices'] if entries[i][b] != rows[i]['label'] and entries[i]['tfidf'] != rows[i]['label']])
            assert expected == result['paired_primary'][str(epoch)]
    write(ART / 'verification.json', dict(status='passed', metrics_recomputed_with_sklearn=checked,
        aligned_prediction_rows=1238, inherited_beto_identities_checked=2476,
        guarded_inputs=len(p['input_guards']), output_files_checked=len(report['output_guards']),
        evaluation_rows_unchanged=218, exact_frozen_partitions=True, paired_errors_verified=True,
        report_sha256=sha(ART / 'report.json'), created_at_utc=now()))
    print(f'Verified {checked} metric summaries; inputs and 218 evaluation rows unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['freeze', 'run', 'verify'])
    globals()[parser.parse_args().mode]()
