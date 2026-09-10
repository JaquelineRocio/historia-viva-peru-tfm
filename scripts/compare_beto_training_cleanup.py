"""One data-cleanup comparison against the saved effective-group-loss reference."""
from __future__ import annotations

import argparse
import math
import time
from collections import Counter
from copy import deepcopy
from hashlib import sha256

from compare_beto_length import ROOT, read, sha, write
from compare_beto_loss_normalization import inputs as reference_inputs, decide, guard, subsets
from compare_beto_source_epochs import now
from compare_tfidf_beto_work_control import score
from verify_external_development import fingerprint

ART = ROOT / 'artifacts/experiments/beto-training-cleanup-v1'
OUT = ROOT / 'outputs/beto-training-cleanup-v1/run'
BUILD = ROOT / 'artifacts/reviews/beto-training-cleanup-v1/build-report.json'
REFERENCE = ROOT / 'outputs/beto-loss-normalization-v1'


def populations():
    parent, indexed, original = reference_inputs()
    build = read(BUILD)
    for g in build['input_guards']:
        assert sha(ROOT / g['path']) == g['sha256'], g['path']
    dataset = read(ROOT / build['dataset']['path'])
    assert guard(ROOT / build['dataset']['path']) == build['dataset']
    mapping = read(ROOT / 'outputs/corpus-snapshot-v4/row-mapping.json')['items']
    assert len(mapping) == len(dataset['items'])
    by_parent = {m['parent_snapshot_index']: dataset['items'][m['candidate_snapshot_index']] for m in mapping}
    rows = deepcopy(original)
    excluded = set(build['quarantine_snapshot_indices'])
    for i, (snapshot_index, row) in enumerate(indexed):
        if snapshot_index not in excluded:
            expected = dict(row)
            if snapshot_index == 49:
                expected['label'] = 'no_relevante'
            assert by_parent[snapshot_index] == expected
            rows[i] = expected
    folds = deepcopy(parent['folds'])
    for fold in folds:
        fold['parent_fit_count'] = fold['fit_count']
        fold['parent_fit_sha256'] = fold['fit_sha256']
        fold['fit_indices'] = [i for i in fold['fit_indices'] if indexed[i][0] not in excluded]
        fold['fit_count'] = len(fold['fit_indices'])
        fold['reliable_primary_indices'] = [i for i in fold['primary_indices'] if indexed[i][0] not in excluded]
        fit = [rows[i] for i in fold['fit_indices']]
        counts = Counter(r['label'] for r in fit)
        assert set(counts) == set(parent['labels'])
        assert not set(fold['fit_indices']) & set(fold['held_indices'])
        assert not {r['resourceId'] for r in fit} & set(fold['held_sources'])
        fold['fit_class_counts'] = dict(counts)
        fold['class_weights'] = {label: len(fit)/(len(counts)*counts[label]) for label in parent['labels']}
        fold['steps_per_epoch'] = math.ceil(math.ceil(len(fit)/parent['candidate_params']['batch_size'])/parent['candidate_params']['gradient_accumulation_steps'])
        fold['fit_sha256'] = fingerprint(fit)
        fold['schedule_total_steps'] = fold['steps_per_epoch'] * 3
        fold['warmup_steps'] = max(1, int(fold['schedule_total_steps'] * .1))
        assert fold['held_sha256'] == fingerprint([rows[i] for i in fold['held_indices']])
    return parent, build, indexed, rows, folds


def groups(fold, rows):
    return dict(subsets(fold, rows), reliable_primary=fold['reliable_primary_indices'])


def baseline_predictions(indexed, name):
    saved = read(REFERENCE / name / 'predictions.json')['items']
    assert len(saved) == len(indexed) == 619
    for i, (entry, (si, row)) in enumerate(zip(saved, indexed)):
        assert (entry['train_index'], entry['snapshot_index'], entry['truth'], entry['text_sha256']) == (
            i, si, row['label'], sha256(row['text'].encode('utf-8')).hexdigest())
    return [entry['candidate'] for entry in saved]


def freeze():
    assert not ART.exists() and not OUT.exists()
    parent, build, indexed, rows, folds = populations()
    checks = read(ROOT / 'artifacts/experiments/beto-loss-normalization-v1/verification.json')
    assert checks['status'] == 'passed'
    assert checks['report_sha256'] == sha(ROOT / 'artifacts/experiments/beto-loss-normalization-v1/report.json')
    preflight = read(ROOT / 'outputs/beto-training-cleanup-v1/preflight.json')
    assert preflight['status'] == 'passed'
    assert preflight['trainer_sha256'] == sha(ROOT / 'scripts/beto_effective_batch_loss.py')
    guarded = {g['path']: g for g in build['input_guards']}
    paths = [BUILD, ROOT / build['dataset']['path'], ROOT / 'outputs/corpus-snapshot-v4/row-mapping.json',
        ROOT / 'outputs/corpus-snapshot-v4/originals-and-decisions.json',
        ROOT / 'artifacts/reviews/beto-training-cleanup-v1/build-verification.json',
        ROOT / 'scripts/compare_beto_training_cleanup.py', ROOT / 'scripts/beto_effective_batch_loss.py',
        ROOT / 'outputs/beto-training-cleanup-v1/preflight.json']
    for fold in folds:
        paths += [REFERENCE / fold['id'] / 'predictions.json', REFERENCE / fold['id'] / 'training-details.json']
        baseline_predictions(indexed, fold['id'])
    for path in paths:
        guarded[path.relative_to(ROOT).as_posix()] = guard(path)
    p = dict(status='frozen_before_training', created_at_utc=now(),
        question='Does the adjudicated cleanup package help with the same effective-group-loss BETO recipe?',
        baseline='Saved beto-loss-normalization-v1 epoch2, not the higher-rate variant or historical microbatch-loss reference.',
        params=parent['candidate_params'], training_config=parent['training_config'], labels=parent['labels'], folds=folds,
        dataset=build['dataset'], training_rows_sha256=build['training_rows_sha256'], input_guards=list(guarded.values()),
        primary='Same original held works and labels including disputed rows. Do not improve scores by deleting difficult evaluation cases.',
        secondary='Reliable primary excludes adjudicated quarantines identically for both predictions, descriptive only. Fit uses common retained rows with the same revised label49 for both models.',
        success_criterion='At least2 additional ideas correct in BOTH full primary works, no decrease in seven-class macro F1 in either, and no decrease in ideas correct on common fit. Exploratory, not significance or model readiness.',
        intervention='Data package only: quarantine, one relabel. Texts unchanged. Derived class weights, shuffle sequence and potentially group sizes follow revised data.',
        invariants='Same pinned base, seed42, lr2e-5, epoch2 with scheduler horizon3, weighted group CE, batch2 accumulation8, 384tokens, AMP, clipping1 and AdamW decay.01.',
        stop='Exactly two new trajectories and two snapshots. No automatic new variants or model promotion.',
        evaluation_policy='No predictions on original validation/test, external31 or pilot22. TRAIN holdouts have been reused and are not independent.',
        limits=['Selected-unit AI adjudication, not complete corpus certification or human gold.',
                'A package comparison cannot isolate removal, relabeling, weight changes or stochastic trajectory effects.'])
    p['content_sha256'] = fingerprint(p)
    ART.mkdir(parents=True)
    write(ART / 'protocol.json', p)
    print('Frozen cleanup comparison', [(f['id'], f['fit_count']) for f in folds], flush=True)


def inputs():
    p = read(ART / 'protocol.json')
    assert p['content_sha256'] == fingerprint({k:v for k,v in p.items() if k != 'content_sha256'})
    for g in p['input_guards']:
        assert sha(ROOT / g['path']) == g['sha256'], g['path']
    parent, build, indexed, rows, folds = populations()
    assert p['folds'] == folds and p['params'] == parent['candidate_params']
    assert p['training_config'] == parent['training_config'] and p['labels'] == parent['labels']
    assert p['dataset'] == build['dataset'] and p['training_rows_sha256'] == build['training_rows_sha256']
    return p, indexed, rows


def run():
    p, indexed, rows = inputs()
    assert not OUT.exists() and not (ART / 'report.json').exists()
    from beto_effective_batch_loss import train_epoch_trajectory
    from app.ml.beto_experiment import predict_beto
    import torch
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    results = {}
    stage = 'start'
    try:
        for fold in p['folds']:
            name = fold['id']
            stage = name + ':training'
            print(name, 'fit', fold['fit_count'], flush=True)
            d = train_epoch_trajectory([rows[i] for i in fold['fit_indices']], p['labels'], p['params'],
                p['training_config'], OUT / name, checkpoint_epochs=(2,))
            write(OUT / name / 'training-details.json', d)
            stage = name + ':inference'
            candidate = predict_beto(OUT / name / 'epoch-2', rows, p['labels'], p['params'])
            baseline = baseline_predictions(indexed, name)
            records = [dict(train_index=i, snapshot_index=si, source=row['resourceId'],
                text_sha256=sha256(row['text'].encode('utf-8')).hexdigest(),
                original_truth=row['label'], truth=rows[i]['label'], baseline=baseline[i], candidate=candidate[i],
                role='fit' if i in fold['fit_indices'] else 'held' if i in fold['held_indices'] else 'quarantined_fit')
                for i, (si, row) in enumerate(indexed)]
            write(OUT / name / 'predictions.json', dict(items=records))
            metrics = {subset:{k:score(rows, pred, ix, p['labels']) for k,pred in [('baseline',baseline),('candidate',candidate)]}
                for subset,ix in groups(fold, rows).items()}
            results[name] = dict(metrics=metrics, training_details=d)
            print(name, 'primary ideas', metrics['primary']['candidate']['confusion_matrix'][2][2], flush=True)
        inputs()
        report = dict(protocol=guard(ART / 'protocol.json'), created_at_utc=now(), folds=results,
            decision=decide(results), trajectories=2, checkpoints=2, prediction_rows=1238,
            seconds=time.perf_counter()-started, cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            output_guards=[guard(path) for path in sorted(OUT.rglob('*')) if path.is_file()],
            production_changed=False, validation_test_external_pilot_predictions=False)
        write(ART / 'report.json', report)
        print(report['decision'], flush=True)
    except Exception as exc:
        write(OUT / 'failure.json', dict(stage=stage, exception=type(exc).__name__, message=str(exc), automatic_retry=False))
        raise


def verify():
    from sklearn.metrics import confusion_matrix, f1_score
    p, indexed, rows = inputs()
    report = read(ART / 'report.json')
    assert report['protocol'] == guard(ART / 'protocol.json')
    for g in report['output_guards']:
        assert sha(ROOT / g['path']) == g['sha256'], g['path']
    checks, counters = 0, {}
    for fold in p['folds']:
        name = fold['id']
        entries = read(OUT / name / 'predictions.json')['items']
        baseline = baseline_predictions(indexed, name)
        assert len(entries) == 619
        for i, (entry, (si, original)) in enumerate(zip(entries, indexed)):
            expected_role = 'fit' if i in fold['fit_indices'] else 'held' if i in fold['held_indices'] else 'quarantined_fit'
            assert (entry['train_index'], entry['snapshot_index'], entry['source'], entry['text_sha256'], entry['original_truth'], entry['truth'], entry['role']) == (
                i, si, original['resourceId'], sha256(original['text'].encode('utf-8')).hexdigest(), original['label'], rows[i]['label'], expected_role)
            assert entry['baseline'] == baseline[i] and entry['candidate'] in p['labels']
        for subset, ix in groups(fold, rows).items():
            truth = [rows[i]['label'] for i in ix]
            for kind, m in report['folds'][name]['metrics'][subset].items():
                pred = [entries[i][kind] for i in ix]
                assert confusion_matrix(truth, pred, labels=p['labels']).tolist() == m['confusion_matrix']
                assert sum(a==b for a,b in zip(truth,pred)) == m['correct'] and len(ix) == m['rows']
                for key, labels in [('f1_macro',m['metric_labels']),('f1_macro_all_seven',p['labels'])]:
                    assert abs(f1_score(truth,pred,labels=labels,average='macro',zero_division=0)-m[key]) < 1e-12
                checks += 1
        d = read(OUT / name / 'training-details.json')
        old = read(REFERENCE / name / 'training-details.json')
        assert d == report['folds'][name]['training_details']
        assert d['class_counts'] == fold['fit_class_counts']
        for label, weight in fold['class_weights'].items():
            assert abs(d['class_weights'][label]-weight) < 1e-6
        for key in ('base_model','resolved_revision','seed','effective_batch_size','max_len','optimizer','weight_decay',
                    'class_weighting','loss_normalization','gradient_clipping_max_norm','gradient_checkpointing',
                    'mixed_precision','offline','local_files_only','schedule_epochs'):
            assert d[key] == old[key], key
        assert d['checkpoint_epochs'] == [2] and d['checkpoint_saves'] == 1 and d['epochs_executed'] == 2
        assert d['steps_per_epoch'] == fold['steps_per_epoch']
        assert d['schedule_total_steps'] == fold['steps_per_epoch']*3
        assert d['warmup_steps'] == max(1,int(d['schedule_total_steps']*.1))
        assert d['optimizer_update_attempts'] == 2*fold['steps_per_epoch'] == d['optimizer_updates']+d['skipped_updates']
        assert d['scheduler_steps'] == d['optimizer_updates']
        cumulative = 0
        for h in d['history']:
            cumulative += h['optimizer_updates']
            total,warmup = d['schedule_total_steps'], d['warmup_steps']
            expected_lr = p['params']['lr']*min((cumulative+1)/warmup,max(0.,(total-cumulative)/max(1,total-warmup)))
            assert abs(h['learning_rate_after_epoch']-expected_lr) < 1e-14
            assert h['optimizer_updates']+h['skipped_updates'] == fold['steps_per_epoch']
        directory = OUT / name / 'epoch-2'
        mapping = {str(i):label for i,label in enumerate(p['labels'])}
        cfg = read(directory / 'config.json')
        assert cfg['id2label'] == mapping and cfg['label2id'] == {l:i for i,l in enumerate(p['labels'])}
        assert read(directory / 'labels.json') == dict(id2label=mapping,max_len=384)
        for filename in ('tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt'):
            assert sha(directory / filename) == sha(REFERENCE / name / 'epoch-2' / filename)
        counters[name] = dict(baseline_updates=old['optimizer_updates'],candidate_updates=d['optimizer_updates'],
            baseline_skips=old['skipped_updates'],candidate_skips=d['skipped_updates'])
    assert report['decision'] == decide(report['folds'])
    write(ART / 'verification.json', dict(status='passed', metric_summaries_recomputed=checks, aligned_rows=1238,
        actual_update_comparison=counters, guarded_inputs=len(p['input_guards']),
        output_files_checked=len(report['output_guards']), full_primary_membership_unchanged=True,
        same_scoring_labels_for_both_models=True, held_source_exclusion_verified=True,
        report_sha256=sha(ART / 'report.json'), created_at_utc=now()))
    print('Verified',checks,'metric summaries',counters,flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze','run','verify'))
    globals()[parser.parse_args().action]()
