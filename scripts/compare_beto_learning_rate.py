"""One predeclared learning-rate intervention on two existing TRAIN holdouts."""
from __future__ import annotations

import argparse
import shutil
import time
from hashlib import sha256

from compare_beto_length import ROOT, read, sha, write
from compare_beto_source_epochs import inputs as parent_inputs, now, metrics, IDEAS
from compare_tfidf_beto_work_control import beto_predictions, score
from verify_external_development import fingerprint

ART = ROOT / 'artifacts/experiments/beto-learning-rate-v1'
OUT = ROOT / 'outputs/beto-learning-rate-v1'
PARENT = ROOT / 'artifacts/experiments/beto-source-epochs-v1/protocol.json'


def guard(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path))


def decide(folds):
    deltas = {}
    for name, fold in folds.items():
        deltas[name] = {}
        for subset in ('fit', 'primary'):
            a, b = (fold['metrics'][subset][k] for k in ('baseline', 'candidate'))
            i = a['labels'].index(IDEAS)
            deltas[name][subset] = dict(ideas_correct=b['confusion_matrix'][i][i]-a['confusion_matrix'][i][i],
                correct=b['correct']-a['correct'], f1_macro_all_seven=b['f1_macro_all_seven']-a['f1_macro_all_seven'])
    if all(d['primary']['ideas_correct'] >= 2 and d['primary']['f1_macro_all_seven'] >= 0
           and d['fit']['ideas_correct'] >= 0 for d in deltas.values()):
        status = 'favorable_exploratory_learning_and_transfer_signal'
    elif all(d['fit']['ideas_correct'] > 0 for d in deltas.values()) and all(d['primary']['ideas_correct'] <= 0 for d in deltas.values()):
        status = 'better_fit_without_ideas_transfer'
    else:
        status = 'criterion_not_met_or_work_dependent'
    return dict(status=status, deltas=deltas, selected_model=None,
                next_action='Stop this intervention; no automatic additional rates, epochs or promotion.')


def freeze():
    assert not ART.exists() and not OUT.exists(), 'No overwrite or repeated experiment'
    parent = read(PARENT)
    indexed = parent_inputs(parent)
    control = read(ROOT / 'artifacts/experiments/tfidf-beto-work-control-v1/protocol.json')
    guards = {g['path']: g for g in control['input_guards']}
    for g in guards.values():
        assert sha(ROOT / g['path']) == g['sha256'], g['path']
    paths = [PARENT, ROOT / 'scripts/compare_beto_learning_rate.py',
             ROOT / 'scripts/beto_epoch_trajectory.py',
             ROOT / 'apps/ml/app/ml/beto_experiment.py',
             ROOT / 'scripts/compare_tfidf_beto_work_control.py',
             ROOT / 'artifacts/experiments/beto-source-epochs-v1/report.json',
             ROOT / 'artifacts/experiments/tfidf-beto-work-control-v1/report.json',
             ROOT / 'artifacts/experiments/tfidf-beto-work-control-v1/protocol.json',
             ROOT / 'artifacts/experiments/tfidf-beto-work-control-v1/verification.json',
             ROOT / 'outputs/beto-source-epochs-v1-preflight.json']
    paths += [ROOT / f"outputs/beto-source-epochs-v1/{f['id']}/training-details.json" for f in parent['folds']]
    guards.update({guard(path)['path']: guard(path) for path in paths})
    preflight = read(ROOT / 'outputs/beto-source-epochs-v1-preflight.json')
    assert preflight['status'] == 'passed'
    assert preflight['trainer_sha256'] == sha(ROOT / 'scripts/beto_epoch_trajectory.py')
    candidate_params = dict(parent['params'], lr=4e-5)
    assert [k for k in candidate_params if candidate_params[k] != parent['params'][k]] == ['lr']
    # Exercise the predeclared decision boundaries before any real training.
    def fixture(fit_delta, held_delta, macro_delta):
        def metric(correct, macro):
            return dict(labels=[IDEAS], confusion_matrix=[[correct]], correct=correct, f1_macro_all_seven=macro)
        return {n: dict(metrics=dict(fit=dict(baseline=metric(5, .5), candidate=metric(5+fit_delta, .5)),
                    primary=dict(baseline=metric(0, .2), candidate=metric(held_delta, .2+macro_delta)))) for n in ('a', 'b')}
    assert decide(fixture(0, 2, 0))['status'] == 'favorable_exploratory_learning_and_transfer_signal'
    assert decide(fixture(1, 1, .1))['status'] == 'criterion_not_met_or_work_dependent'
    assert decide(fixture(1, 2, -.01))['status'] == 'criterion_not_met_or_work_dependent'
    assert decide(fixture(-1, 2, .1))['status'] == 'criterion_not_met_or_work_dependent'
    assert decide(fixture(1, 0, .1))['status'] == 'better_fit_without_ideas_transfer'
    import torch
    assert torch.cuda.is_available() and shutil.disk_usage(ROOT).free > 1_500_000_000
    protocol = dict(status='frozen_before_training', created_at_utc=now(), parent=guard(PARENT),
        question='Does doubling learning rate improve fit and transfer of ideas at the same fixed epoch?',
        rationale='Partial BETO fit and TF-IDF recovery of some held ideas justify one optimization probe. The doubled value is a predeclared intervention, not a proven optimal rate.',
        baseline_params=parent['params'], candidate_params=candidate_params, changed_parameter='lr',
        checkpoint_epochs=[2], schedule_epochs=3, folds=parent['folds'], labels=parent['labels'],
        training_config=parent['training_config'], packages=parent['packages'],
        training_rows_sha256=parent['training_rows_sha256'], evaluation_sha256=control['evaluation_sha256'],
        input_guards=list(guards.values()), decision_boundary_checks=5,
        success_criterion='In BOTH primary works: at least 2 additional ideas correct and no decrease in seven-class macro F1; fit ideas correct must not decrease in either round. Exploratory threshold, not significance or readiness.',
        primary_comparison='Saved baseline epoch2 versus new epoch2, identical TRAIN rows and fold membership. No selection against baseline epoch3 or TF-IDF.',
        invariants='Same offline base/revision, seed42, labels/order/texts, batch2 accumulation8, inverse weights, microbatch CE normalization, AdamW decay.01, clipping1, AMP, checkpointing, 384 tokens, scheduler horizon3 and warmup. Same trainer; stop at epoch2.',
        counters_policy='Record actual AMP skips and optimizer updates; numerical trajectories can differ as a consequence of lr. Do not claim equal actual updates without checking.',
        stop='Exactly two fresh base trajectories, one per fold, one snapshot each. No retraining baseline, automatic retries, third epoch, additional rate or model promotion.',
        limits=['Reused TRAIN holdouts, not independent evaluation.', 'One rate and one seed do not prove a unique cause or general BETO capacity.',
                'Corpus, guide and three proposed corrections unchanged; no validation/test/external31 predictions.'])
    protocol['content_sha256'] = fingerprint(protocol)
    ART.mkdir(parents=True)
    write(ART / 'protocol.json', protocol)
    print('Frozen: lr2e-5 -> 4e-5, epoch2, two folds; 5 decision checks passed.', flush=True)


def inputs():
    p = read(ART / 'protocol.json')
    assert fingerprint({k: v for k, v in p.items() if k != 'content_sha256'}) == p['content_sha256']
    for g in p['input_guards']:
        assert sha(ROOT / g['path']) == g['sha256'], g['path']
    parent = read(PARENT)
    indexed = parent_inputs(parent)
    assert p['folds'] == parent['folds'] and p['baseline_params'] == parent['params']
    assert p['candidate_params'] == dict(parent['params'], lr=4e-5)
    data = read(ROOT / parent['dataset'])
    assert fingerprint([r for r in data['items'] if r['split'] != 'train']) == p['evaluation_sha256']
    return p, indexed, [r for _, r in indexed]


def subsets(fold, rows):
    return dict(fit=fold['fit_indices'], held=fold['held_indices'], primary=fold['primary_indices'],
                **{s: [i for i in fold['held_indices'] if rows[i]['resourceId'] == s]
                   for s in fold['held_sources'] if s != fold['primary_source']})


def run():
    p, indexed, rows = inputs()
    assert not OUT.exists() and not (ART / 'report.json').exists()
    from beto_epoch_trajectory import train_epoch_trajectory
    from app.ml.beto_experiment import predict_beto
    import torch
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    OUT.mkdir(parents=True)
    results = {}
    started = time.perf_counter()
    stage = 'start'
    try:
        for fold in p['folds']:
            name = fold['id']
            stage = name + ':training'
            print(name, 'fit', fold['fit_count'], 'lr', p['candidate_params']['lr'], flush=True)
            details = train_epoch_trajectory([rows[i] for i in fold['fit_indices']], p['labels'],
                p['candidate_params'], p['training_config'], OUT / name, checkpoint_epochs=(2,))
            write(OUT / name / 'training-details.json', details)
            stage = name + ':inference'
            directory = OUT / name / 'epoch-2'
            candidate = predict_beto(directory, rows, p['labels'], p['candidate_params'])
            baseline = beto_predictions(indexed, fold)['beto_epoch2']
            records = [dict(train_index=i, snapshot_index=si, source=r['resourceId'], truth=r['label'],
                text_sha256=sha256(r['text'].encode('utf-8')).hexdigest(),
                role='fit' if i in fold['fit_indices'] else 'held', baseline=baseline[i], candidate=candidate[i])
                for i, (si, r) in enumerate(indexed)]
            write(OUT / name / 'predictions.json', dict(items=records))
            scores = {subset: {k: score(rows, pred, ix, p['labels']) for k, pred in
                [('baseline', baseline), ('candidate', candidate)]} for subset, ix in subsets(fold, rows).items()}
            results[name] = dict(metrics=scores, training_details=details)
            print(name, 'primary ideas', scores['primary']['candidate']['confusion_matrix'][2][2], flush=True)
        inputs()
        report = dict(created_at_utc=now(), protocol=guard(ART / 'protocol.json'), folds=results,
            decision=decide(results), output_guards=[guard(path) for path in sorted(OUT.rglob('*')) if path.is_file()],
            new_training_trajectories=2, new_checkpoints=2, new_prediction_rows=1238,
            elapsed_seconds=time.perf_counter()-started, cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(), corpus_changed=False,
            test_predictions=False, validation_predictions=False, external_predictions=False, production_changed=False)
        write(ART / 'report.json', report)
        print(report['decision'], flush=True)
    except Exception as exc:
        write(OUT / 'failure.json', dict(stage=stage, type=type(exc).__name__, message=str(exc), automatic_retry=False))
        raise


def verify():
    from sklearn.metrics import confusion_matrix, f1_score
    p, indexed, rows = inputs()
    report = read(ART / 'report.json')
    assert report['protocol'] == guard(ART / 'protocol.json')
    for g in report['output_guards']:
        assert sha(ROOT / g['path']) == g['sha256']
    checks = 0
    counters = {}
    for fold in p['folds']:
        name = fold['id']
        result = report['folds'][name]
        entries = read(OUT / name / 'predictions.json')['items']
        baseline = beto_predictions(indexed, fold)['beto_epoch2']
        assert len(entries) == 619
        for i, (entry, (si, r)) in enumerate(zip(entries, indexed)):
            assert (entry['train_index'], entry['snapshot_index'], entry['source'], entry['truth'], entry['text_sha256'], entry['role']) == (i, si, r['resourceId'], r['label'], sha256(r['text'].encode('utf-8')).hexdigest(), 'fit' if i in fold['fit_indices'] else 'held')
            assert entry['baseline'] == baseline[i] and entry['candidate'] in p['labels']
        for subset, ix in subsets(fold, rows).items():
            truth = [rows[i]['label'] for i in ix]
            for k, m in result['metrics'][subset].items():
                pred = [entries[i][k] for i in ix]
                assert confusion_matrix(truth, pred, labels=p['labels']).tolist() == m['confusion_matrix']
                assert sum(a == b for a, b in zip(truth, pred)) == m['correct']
                for key, labels in [('f1_macro', m['metric_labels']), ('f1_macro_all_seven', p['labels'])]:
                    assert abs(f1_score(truth, pred, labels=labels, average='macro', zero_division=0)-m[key]) < 1e-12
                checks += 1
        d = read(OUT / name / 'training-details.json')
        old = read(ROOT / f'outputs/beto-source-epochs-v1/{name}/training-details.json')
        assert d == result['training_details']
        for key in ('base_model', 'resolved_revision', 'class_counts', 'class_weights', 'schedule_epochs',
                    'steps_per_epoch', 'schedule_total_steps', 'warmup_steps', 'seed', 'effective_batch_size',
                    'max_len', 'optimizer', 'weight_decay', 'class_weighting', 'loss_normalization',
                    'gradient_clipping_max_norm', 'gradient_checkpointing', 'mixed_precision', 'offline', 'local_files_only'):
            assert d[key] == old[key], key
        assert d['checkpoint_epochs'] == [2] and d['checkpoint_saves'] == 1 and d['epochs_executed'] == 2
        assert d['optimizer_update_attempts'] == 2*fold['steps_per_epoch']
        assert d['optimizer_updates'] + d['skipped_updates'] == d['optimizer_update_attempts']
        assert d['scheduler_steps'] == d['optimizer_updates']
        cumulative = 0
        for history in d['history']:
            cumulative += history['optimizer_updates']
            total, warmup = d['schedule_total_steps'], d['warmup_steps']
            expected = p['candidate_params']['lr'] * min((cumulative+1)/warmup, max(0., (total-cumulative)/max(1, total-warmup)))
            assert abs(history['learning_rate_after_epoch']-expected) < 1e-14
            assert history['optimizer_updates'] + history['skipped_updates'] == fold['steps_per_epoch']
        counters[name] = dict(baseline_updates=sum(h['optimizer_updates'] for h in old['history'][:2]),
            candidate_updates=d['optimizer_updates'], baseline_skips=sum(h['skipped_updates'] for h in old['history'][:2]), candidate_skips=d['skipped_updates'])
        directory = OUT / name / 'epoch-2'
        cfg = read(directory / 'config.json')
        mapping = {str(i): l for i, l in enumerate(p['labels'])}
        assert cfg['id2label'] == mapping and cfg['label2id'] == {l: i for i, l in enumerate(p['labels'])}
        assert read(directory / 'labels.json') == dict(id2label=mapping, max_len=384)
        for token_file in ('tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt'):
            assert sha(directory / token_file) == sha(ROOT / f'outputs/beto-source-epochs-v1/{name}/epoch-2' / token_file)
    assert report['decision'] == decide(report['folds'])
    write(ART / 'verification.json', dict(status='passed', metric_summaries_recomputed=checks,
        aligned_rows=1238, evaluation_rows_unchanged=218, guarded_inputs=len(p['input_guards']),
        output_files_checked=len(report['output_guards']), actual_update_comparison=counters,
        single_config_change='lr2e-5 -> 4e-5', baseline_epoch=2, candidate_epoch=2,
        label_maps_tokenizers_and_scheduler_verified=True, decision_verified=True,
        report_sha256=sha(ART / 'report.json'), created_at_utc=now()))
    print('Verification passed', checks, 'metric summaries', counters, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run', 'verify'))
    globals()[parser.parse_args().action]()
