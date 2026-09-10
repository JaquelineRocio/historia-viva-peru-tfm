"""Two frozen TRAIN work-group holdouts, epochs 2/3; no model selection."""
from __future__ import annotations

import argparse
import importlib.metadata
import math
import re
import shutil
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256

from compare_beto_length import ROOT, metric_report, read, sha, write
from verify_external_development import fingerprint, workspace_file

ARTIFACTS = ROOT / 'artifacts/experiments/beto-source-epochs-v1'
OUTPUT = ROOT / 'outputs/beto-source-epochs-v1'
DATASET = 'outputs/corpus-snapshot-v3/reviewed-export.json'
IDEAS = 'crisis_ideas_emancipadoras'
PARAMS = dict(lr=2e-5, epochs=3, batch_size=2, gradient_accumulation_steps=8, max_len=384)
EPOCHS = [2, 3]
OPHELAN = '0ea45102-057d-4bff-b527-f36326f66d33'
HUAMANGA = '9fecbe5a-9fb2-4002-a088-8a2810db938e'
MORAN = '1c8bc7af-a9f6-5392-b3ff-6d7433fb010a'
GROUPS = [dict(id='ophelan_huamanga', primary_source=OPHELAN, held_sources=[OPHELAN, HUAMANGA]),
          dict(id='moran', primary_source=MORAN, held_sources=[MORAN])]


def require(value, message):
    if not value:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def guard(path):
    return dict(path=path, sha256=sha(workspace_file(path)))


def train_only(payload):
    return [(i, row) for i, row in enumerate(payload['items']) if row['split'] == 'train']


def normalized(text):
    text = unicodedata.normalize('NFKD', text.casefold()).replace('\u00ad', '')
    return ' '.join(re.findall(r'\w+', ''.join(c for c in text if not unicodedata.combining(c))))


def make_folds(rows, labels, groups=GROUPS):
    require(rows and all(r['split'] == 'train' for r in rows), 'Only TRAIN rows allowed')
    require(len(set(labels)) == len(labels) and set(r['label'] for r in rows) == set(labels), 'Taxonomy differs')
    folds = []
    already_held = set()
    for group in groups:
        held_sources = set(group['held_sources'])
        require(group['primary_source'] in held_sources and not held_sources & already_held,
                'Primary missing or overlapping held groups')
        already_held.update(held_sources)
        fit = [i for i, row in enumerate(rows) if row['resourceId'] not in held_sources]
        held = [i for i, row in enumerate(rows) if row['resourceId'] in held_sources]
        primary = [i for i in held if rows[i]['resourceId'] == group['primary_source']]
        require(fit and held and primary and {rows[i]['resourceId'] for i in held} == held_sources,
                'Missing work or empty partition')
        require({rows[i]['label'] for i in fit} == set(labels), 'Fit partition lacks a class')
        require(not {normalized(rows[i]['text']) for i in fit} &
                {normalized(rows[i]['text']) for i in held}, 'Exact cross-partition duplicate')
        counts = dict(Counter(rows[i]['label'] for i in fit))
        steps = math.ceil(math.ceil(len(fit) / 2) / 8)
        folds.append(dict(**group, fit_indices=fit, held_indices=held, primary_indices=primary,
                          fit_count=len(fit), held_count=len(held), primary_count=len(primary),
                          fit_sha256=fingerprint([rows[i] for i in fit]),
                          held_sha256=fingerprint([rows[i] for i in held]),
                          fit_class_counts=counts,
                          class_weights={label: len(fit) / (len(labels) * counts[label]) for label in labels},
                          steps_per_epoch=steps, schedule_total_steps=steps * 3,
                          warmup_steps=max(1, int(steps * 3 * .1))))
    return folds


def dependency_screen(indexed):
    rows = [r for _, r in indexed]
    phrases = ['diario secreto', 'lopez aldana', 'reflexiones filantropicas', 'burzio',
               'gaceta de buenos aires', 'gaceta del gobierno', 'phelan', 'independencia concedida']
    hits = {phrase: [dict(snapshot_index=indexed[i][0], source=r['resourceId'])
                     for i, r in enumerate(rows) if phrase in normalized(r['text'])] for phrase in phrases}
    grams = defaultdict(set)
    for i, row in enumerate(rows):
        words = normalized(row['text']).split()
        for j in range(len(words) - 19):
            grams[tuple(words[j:j + 20])].add(i)
    overlaps = {}
    for group in GROUPS:
        sources = set(group['held_sources'])
        matches = set()
        for indices in grams.values():
            held = [i for i in indices if rows[i]['resourceId'] in sources]
            fit = [i for i in indices if rows[i]['resourceId'] not in sources]
            matches.update((indexed[i][0], indexed[j][0]) for i in held for j in fit)
        overlaps[group['id']] = sorted(matches)
    return dict(method='TRAIN only: accent/punctuation/soft-hyphen normalized phrase and 20-word span screen',
                phrase_hits=hits, cross_partition_20_word_spans=overlaps,
                adjudication=[
                    'O\u2019Phelan1985 and Huamanga/Pereyra held together: TRAIN snapshot74,78,276 use arguments at pp188,173,189; snapshot352 identifies the exact 1985 article in bibliography. This is more than shared authorship. All57 Huamanga rows excluded from fit; O\u2019Phelan103 remains the primary outcome.',
                    'Moran18 retained together, including Diario Secreto and reproduced primary documents. Screen did not identify a second TRAIN work carrying those specific passages. No claim of exhaustive documentary independence.',
                    'Other independencia concedida hits were read at TRAIN snapshot45(Fonseca),418/676/697(video): discussion of Bonilla/Spalding or broad historiographic positions, not identified reproductions of the O\u2019Phelan article. Shared thesis alone does not merge these works.',
                    'Existing Hunefeldt/Fonseca, Contreras/video and Hampe/Basadre relations stay on the fit side in both folds. Shared topic or bibliographic name alone is not proof of duplicated evidence.'
                ], limits='AI-assisted documentary review; lexical absence does not rule out paraphrase, OCR loss, shared primary documents or common arguments.')


def inputs(protocol):
    require(protocol['content_sha256'] == fingerprint({k: v for k, v in protocol.items() if k != 'content_sha256'}),
            'Frozen protocol changed')
    require(protocol['status'] == 'frozen_before_training' and protocol['params'] == PARAMS
            and protocol['checkpoint_epochs'] == EPOCHS and protocol['groups'] == GROUPS,
            'Unsupported experiment')
    for entry in protocol['input_guards']:
        require(sha(workspace_file(entry['path'])) == entry['sha256'], 'Changed input: ' + entry['path'])
    for name, version in protocol['packages'].items():
        require(importlib.metadata.version(name) == version, 'Changed package: ' + name)
    from huggingface_hub.constants import HF_HUB_CACHE
    from pathlib import Path
    cfg = protocol['training_config']
    base = Path(HF_HUB_CACHE) / ('models--' + cfg['base_model'].replace('/', '--')) / 'snapshots' / cfg['revision']
    for entry in protocol['base_cache_files']:
        require(Path(entry['name']).name == entry['name'] and sha(base / entry['name']) == entry['file_sha256'],
                'Pinned offline base changed')
    data = read(workspace_file(DATASET))
    require(data['labels'] == protocol['labels'], 'Taxonomy changed')
    indexed = train_only(data)
    del data
    rows = [row for _, row in indexed]
    require(len(rows) == 619 and fingerprint(rows) == protocol['training_rows_sha256'], 'TRAIN membership/order changed')
    require(make_folds(rows, protocol['labels']) == protocol['folds'], 'Partition differs')
    return indexed


def freeze():
    require(not ARTIFACTS.exists() and not OUTPUT.exists(), 'Experiment already exists; no repeat or overwrite')
    parent = read(workspace_file('artifacts/experiments/beto-data-v3/protocol.json'))
    indexed = train_only(read(workspace_file(DATASET)))
    rows = [r for _, r in indexed]
    require(fingerprint(rows) == parent['training_rows_sha256'], 'Parent TRAIN differs')
    guards = {}
    for name in ['beto-length-v1', 'beto-data-v3', 'beto-training-fit-v1']:
        folder = 'artifacts/experiments/' + name + '/'
        prior, result = read(workspace_file(folder + 'protocol.json')), read(workspace_file(folder + 'report.json'))
        require(result['protocol']['sha256'] == sha(workspace_file(folder + 'protocol.json')), 'Parent link differs')
        for entry in prior['input_guards'] + result.get('candidate_files', []) + result.get('prediction_files', []):
            require(sha(workspace_file(entry['path'])) == entry['sha256'], 'Historical input changed')
            guards[entry['path']] = entry
        for path in [folder + 'protocol.json', folder + 'report.json']:
            guards[path] = guard(path)
    # Hash-only protection of external artifacts; do not pass their text to diagnostic/model code.
    external = read(workspace_file(parent['external_dataset']))
    for entry in external['local_input_guards']:
        require(sha(workspace_file(entry['path'])) == entry['sha256'], 'External guard differs')
        guards[entry['path']] = entry
    del external
    for path in [DATASET, 'scripts/beto_epoch_trajectory.py', 'scripts/compare_beto_source_epochs.py',
                 'scripts/check_beto_source_epochs.py', 'scripts/verify_beto_source_epochs.py',
                 'artifacts/experiments/source-generalization-v1/report.json',
                 'outputs/beto-source-epochs-v1-preflight.json']:
        guards[path] = guard(path)
    preflight = read(workspace_file('outputs/beto-source-epochs-v1-preflight.json'))
    require(preflight['status'] == 'passed', 'Synthetic checks have not passed')
    require(preflight['trainer_sha256'] == sha(ROOT / 'scripts/beto_epoch_trajectory.py')
            and preflight['runner_sha256'] == sha(ROOT / 'scripts/compare_beto_source_epochs.py'),
            'Implementation changed after synthetic checks')
    screen = dependency_screen(indexed)
    require(not any(screen['cross_partition_20_word_spans'].values()), 'Unresolved lexical dependency')
    import torch
    require(torch.cuda.is_available(), 'CUDA required; no CPU fallback')
    require(shutil.disk_usage(ROOT).free > 3_000_000_000, 'Insufficient disk space')
    protocol = dict(schema_version=1, id='beto-source-epochs-v1', status='frozen_before_training',
        created_at_utc=now(), question='Does ideas recognition transfer to held work groups, and does epoch3 improve both fit and the primary held work over epoch2?',
        dataset=DATASET, training_rows_sha256=fingerprint(rows), labels=parent['labels'],
        params=PARAMS, checkpoint_epochs=EPOCHS, training_config=parent['training_config'],
        packages=parent['packages'], base_cache_files=parent['base_cache_files'],
        groups=GROUPS, folds=make_folds(rows, parent['labels']), dependency_audit=screen,
        prior_evidence='Existing training-fit and TFIDF source reports motivated these two works; their scores are not independent benchmarks or model selection thresholds.',
        outcome='Primary: paired epoch2-to3 change in ideas correct count/recall, separately on fit and on primary held work. Secondary: ideas precision/F1 and all-class confusion, counts, supported-label macro, per-work results. Huamanga is a separate secondary held work; no pooled headline across rounds.',
        decision_rule=dict(both_folds_improve_fit_and_primary_ideas='exploratory_signal_of_additional_learning_and_transfer',
                           both_folds_improve_fit_ideas_without_primary_gain='transfer_difficulty_persists',
                           otherwise='inconclusive_or_work_dependent', threshold='strict positive integer correct-count delta; no significance or practical-quality claim; no selected epoch'),
        trajectory_policy='Two fresh base initializations. Train continuously for3 epochs; save2and3; no inference between training epochs. Evaluate all snapshots only after their trajectory has finished.',
        recipe_policy='Preserve weighted CE mean per microbatch / actual accumulation group size, AdamW2e-5 decay.01 clipping1 AMPfp16 gradient checkpointing. Recompute inverse class weights and 3-epoch scheduler horizon from each fit partition; record effective updates/skips, not equal budgets between folds.',
        resource_policy=dict(offline=True, cuda_device=torch.cuda.get_device_name(), modal=False, paid_services=False,
                             estimated_execution_minutes=[3, 6], approximate_checkpoint_bytes=1_800_000_000,
                             on_failure='Record stage and stop; no automatic retry or recipe change'),
        limits=['Exploratory TRAIN holdouts chosen using prior diagnostics; not independent final evaluation.',
                'One seed, only two primary works and one additional dependent held work; class supports differ.',
                'Annotation and documentary review assisted by AI, not independent human gold.',
                'Withholding sources changes amount, class weights, data order and scheduler; does not isolate style, labels or memorization.',
                'Epoch3 tests this one extra training interval, not every form of incomplete learning.',
                'No original validation/test or external31 inference or semantic selection; no new labels, deployment or model selection.'],
        input_guards=list(guards.values()))
    protocol['content_sha256'] = fingerprint(protocol)
    inputs(protocol)
    ARTIFACTS.mkdir(parents=True, exist_ok=False)
    write(ARTIFACTS / 'protocol.json', protocol)
    print('Frozen', sha(ARTIFACTS / 'protocol.json'), flush=True)


def metrics(rows, predictions, labels):
    return metric_report([r['label'] for r in rows], predictions, labels,
                         [label for label in labels if any(r['label'] == label for r in rows)])


def decision(folds):
    deltas = {}
    for name, fold in folds.items():
        deltas[name] = {}
        for subset in ['fit', 'primary']:
            values = []
            for epoch in ['2', '3']:
                m = fold['epochs'][epoch][subset]
                i = m['labels'].index(IDEAS)
                values.append(m['confusion_matrix'][i][i])
            deltas[name][subset] = values[1] - values[0]
    if all(d['fit'] > 0 and d['primary'] > 0 for d in deltas.values()):
        status = 'exploratory_signal_of_additional_learning_and_transfer'
    elif all(d['fit'] > 0 and d['primary'] <= 0 for d in deltas.values()):
        status = 'transfer_difficulty_persists'
    else:
        status = 'inconclusive_or_work_dependent'
    return dict(status=status, ideas_correct_deltas=deltas, selected_model=None, selected_epoch=None)


def run():
    require(not OUTPUT.exists() and not (ARTIFACTS / 'report.json').exists(), 'Run already exists; no repeat')
    protocol_path = ARTIFACTS / 'protocol.json'
    protocol_hash = sha(protocol_path)
    protocol = read(protocol_path)
    indexed = inputs(protocol)
    import torch
    from beto_epoch_trajectory import train_epoch_trajectory
    from app.ml.beto_experiment import predict_beto
    require(torch.cuda.is_available(), 'CUDA required; no CPU fallback')
    torch.set_num_threads(4)
    rows = [r for _, r in indexed]
    labels = protocol['labels']
    OUTPUT.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    folds, checkpoint_files, prediction_files = {}, [], []
    stage = 'start'
    try:
        for fold in protocol['folds']:
            name = fold['id']
            stage = name + ':training'
            fit = [rows[i] for i in fold['fit_indices']]
            print(name, 'fit', len(fit), 'held', fold['held_count'], flush=True)
            details = train_epoch_trajectory(fit, labels, PARAMS, protocol['training_config'], OUTPUT / name, EPOCHS)
            write(OUTPUT / name / 'training-details.json', details)
            require(details['resolved_revision'] == protocol['training_config']['revision']
                    and details['checkpoint_saves'] == 2 and details['epochs_executed'] == 3
                    and details['schedule_total_steps'] == fold['schedule_total_steps']
                    and details['warmup_steps'] == fold['warmup_steps']
                    and details['class_counts'] == fold['fit_class_counts']
                    and details['optimizer_update_attempts'] == fold['steps_per_epoch'] * 3
                    and details['scheduler_steps'] == details['optimizer_updates'], 'Executed recipe differs')
            epochs = {}
            for epoch in EPOCHS:
                stage = name + ':inference_epoch' + str(epoch)
                directory = OUTPUT / name / ('epoch-' + str(epoch))
                mapping = {str(i): label for i, label in enumerate(labels)}
                config = read(directory / 'config.json')
                require(config['id2label'] == mapping and config['label2id'] == {v: int(k) for k, v in mapping.items()},
                        'Model label map differs')
                require(read(directory / 'labels.json') == dict(id2label=mapping, max_len=384), 'Inference length differs')
                for token_file in ['tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt']:
                    require(sha(directory / token_file) == sha(ROOT / 'outputs/beto-data-v3/run/candidate' / token_file),
                            'Tokenizer differs')
                # Only the619 original TRAIN rows reach inference; membership is marked per fold.
                predicted = predict_beto(directory, rows, labels, PARAMS)
                require(len(predicted) == len(rows), 'Prediction count differs')
                fit_indices = set(fold['fit_indices'])
                records = [dict(train_index=i, snapshot_index=indexed[i][0], source=row['resourceId'],
                                text_sha256=sha256(row['text'].encode('utf-8')).hexdigest(),
                                truth=row['label'], predicted=predicted[i],
                                role='fit' if i in fit_indices else 'held') for i, row in enumerate(rows)]
                prediction_path = OUTPUT / name / f'epoch-{epoch}-predictions.json'
                write(prediction_path, dict(items=records))
                prediction_files.append(guard(prediction_path.relative_to(ROOT).as_posix()))
                result = {}
                for subset, indices in [('fit', fold['fit_indices']), ('held', fold['held_indices']),
                                        ('primary', fold['primary_indices'])]:
                    result[subset] = metrics([rows[i] for i in indices], [predicted[i] for i in indices], labels)
                result['per_source'] = {s: metrics([r for r in rows if r['resourceId'] == s],
                    [predicted[i] for i, r in enumerate(rows) if r['resourceId'] == s], labels)
                    for s in sorted({r['resourceId'] for r in rows})}
                epochs[str(epoch)] = result
                checkpoint_files.extend(guard(p.relative_to(ROOT).as_posix()) for p in sorted(directory.iterdir()) if p.is_file())
            folds[name] = dict(training_details=details, epochs=epochs)
        stage = 'final_integrity'
        inputs(protocol)
        require(sha(protocol_path) == protocol_hash, 'Protocol changed during run')
        report = dict(schema_version=1, purpose='two_TRAIN_group_holdouts_fixed_epoch_contrast', created_at_utc=now(),
            protocol=dict(path=protocol_path.relative_to(ROOT).as_posix(), sha256=protocol_hash),
            folds=folds, decision=decision(folds), checkpoint_files=checkpoint_files, prediction_files=prediction_files,
            new_training_trajectories=2, checkpoints_saved=4, new_inference_rows=2476, model_loads_for_inference=4,
            old_validation_predictions_performed=False, test_predictions_performed=False,
            external_predictions_performed=False, labels_changed=False, production_changed=False, offline=True,
            inputs_unchanged=True, elapsed_seconds=round(time.perf_counter() - started, 2),
            cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(), cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            limits=protocol['limits'])
        write(OUTPUT / 'report.json', report)
        write(ARTIFACTS / 'report.json', report)
        print(report['decision'], 'seconds', report['elapsed_seconds'], flush=True)
        return report
    except Exception as exc:
        write(OUTPUT / 'failure.json', dict(stage=stage, type=type(exc).__name__, message=str(exc),
              automatic_retry=False, elapsed_seconds=round(time.perf_counter() - started, 2)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'run'])
    action = parser.parse_args().action
    freeze() if action == 'freeze' else run()
