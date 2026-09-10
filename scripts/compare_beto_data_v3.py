"""One predeclared, offline data comparison; reuse the saved 384-token baseline."""
from __future__ import annotations

import argparse
import importlib.metadata
import math
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from compare_beto_length import ROOT, decide, read, sha, summarize, write
from verify_external_development import fingerprint, verify, workspace_file

PROTOCOL = ROOT / 'artifacts/experiments/beto-data-v3/protocol.json'
OUTPUT = ROOT / 'outputs/beto-data-v3/run'
DATASET = 'outputs/corpus-snapshot-v3/reviewed-export.json'
PRIOR = 'artifacts/experiments/beto-length-v1/report.json'
PARAMS = dict(lr=2e-5, epochs=3, batch_size=2, gradient_accumulation_steps=8, max_len=384)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def guard(relative):
    return dict(path=relative, sha256=sha(workspace_file(relative)))


def inputs(protocol):
    """Check membership before the trainer receives only train rows."""
    for entry in protocol['input_guards']:
        require(sha(workspace_file(entry['path'])) == entry['sha256'], 'Changed input: ' + entry['path'])
    payload = read(workspace_file(protocol['training_dataset']))
    require(payload['labels'] == protocol['labels'], 'Training taxonomy differs')
    train = [row for row in payload['items'] if row['split'] == 'train']
    require(len(train) == 619 and fingerprint(train) == protocol['training_rows_sha256'],
            'Training membership, text, labels or order differs')
    require(dict(Counter(row['split'] for row in payload['items'])) == {'train': 619, 'val': 81, 'test': 137},
            'Snapshot split counts differ')
    del payload
    external = read(workspace_file(protocol['external_dataset']))
    verify(external, check_local_inputs=True)
    require(external['content_sha256'] == protocol['external_content_sha256'], 'External set changed')
    require(len(external['items']) == 31 and external['labels'] == protocol['labels'], 'External support differs')
    prior = read(workspace_file(PRIOR))
    require(prior['training_details']['max_len'] == 384 and prior['training_details']['checkpoint_epoch'] == 2,
            'Baseline recipe mismatch')
    pairs = prior['per_item']
    require(len(pairs) == 31, 'Saved baseline predictions incomplete')
    for row, paired in zip(external['items'], pairs):
        require((row['id'], row['resourceId'], row['text_sha256'], row['label']) ==
                (paired['id'], paired['source'], paired['text_sha256'], paired['truth']),
                'Baseline prediction identity or order differs')
    before = [row['after'] for row in pairs]
    require(summarize(external['items'], before, protocol) == prior['after'], 'Baseline metrics differ')
    return train, external['items'], before


def check_protocol(protocol):
    require(protocol['content_sha256'] == fingerprint({k: v for k, v in protocol.items() if k != 'content_sha256'}),
            'Protocol content hash differs')
    require(protocol['status'] == 'frozen_before_training_and_candidate_predictions', 'Protocol not frozen')
    require(protocol['candidate_params'] == protocol['baseline_params'] == PARAMS and protocol['checkpoint_epoch'] == 2,
            'Only the fixed data comparison is supported')
    old = read(workspace_file('artifacts/experiments/beto-length-v1/protocol.json'))
    require(protocol['training_config'] == old['training_config'], 'Base model/revision/seed differs')
    for package, version in protocol['packages'].items():
        require(importlib.metadata.version(package) == version, 'Changed package: ' + package)
    from huggingface_hub.constants import HF_HUB_CACHE
    config = protocol['training_config']
    cached = Path(HF_HUB_CACHE) / ('models--' + config['base_model'].replace('/', '--')) / 'snapshots' / config['revision']
    for entry in protocol['base_cache_files']:
        require(Path(entry['name']).name == entry['name'] and sha(cached / entry['name']) == entry['file_sha256'],
                'Pinned base cache differs')
    return inputs(protocol)


def freeze():
    require(not PROTOCOL.exists() and not OUTPUT.exists(), 'Protocol/run already exists; no automatic new trial')
    old = read(workspace_file('artifacts/experiments/beto-length-v1/protocol.json'))
    prior = read(workspace_file(PRIOR))
    payload = read(workspace_file(DATASET))
    train = [row for row in payload['items'] if row['split'] == 'train']
    reference = read(workspace_file('artifacts/datasets/gold-v1-source-aware.json'))
    original_train = [row for row in reference['items'] if row['split'] == 'train']
    del reference
    require(len(original_train) == 596 and fingerprint(original_train) == old['training_rows_sha256'],
            'Original baseline training rows differ from its frozen protocol')
    require(old['candidate_params'] == PARAMS
            and prior['protocol']['sha256'] == sha(workspace_file('artifacts/experiments/beto-length-v1/protocol.json')),
            'Baseline report/protocol link or parameters differ')
    local_prior = workspace_file('outputs/beto-length-v1/run/report.json')
    require(sha(local_prior) == prior['local_execution_report']['sha256']
            and read(local_prior)['per_item'] == prior['per_item'], 'Baseline execution report differs')
    def identity_counts(items):
        return Counter((row['resourceId'], row['text'], row['label']) for row in items)
    original_identities, candidate_identities = identity_counts(original_train), identity_counts(train)
    external = read(workspace_file(old['external_dataset']))
    import torch
    require(torch.cuda.is_available(), 'CUDA required; no automatic CPU fallback')
    free, total = torch.cuda.mem_get_info()
    # Preserve the recipe, including dataset-dependent class weights and schedule.
    microbatches = math.ceil(len(train) / PARAMS['batch_size'])
    steps = math.ceil(microbatches / PARAMS['gradient_accumulation_steps'])
    paths = [DATASET, PRIOR, 'outputs/beto-length-v1/run/report.json',
             'outputs/corpus-snapshot-v3/build-report.json',
             'outputs/corpus-snapshot-v3/replacement-archive.json',
             'artifacts/experiments/beto-length-v1/protocol.json',
             old['external_dataset'], 'artifacts/datasets/gold-v1-source-aware.json',
             'outputs/corpus-snapshot-v2/reviewed-export.json',
             'artifacts/reviews/boundary-resolution-v3.json', 'artifacts/reviews/training-batch-v3.json',
             'outputs/boundary-resolution-v3/proposed-replacements.json',
             'scripts/build_training_batch_v3.py', 'scripts/compare_beto_data_v3.py',
             'scripts/compare_beto_length.py', 'scripts/beto_fixed_epoch.py',
             'scripts/verify_external_development.py', 'apps/ml/app/ml/beto_experiment.py',
             'scripts/compare_beto_validation.py']
    for entry in prior['candidate_files']:
        require(sha(workspace_file(entry['path'])) == entry['sha256'], 'Saved baseline checkpoint changed')
        paths.append(entry['path'])
    protocol = dict(
        schema_version=1, id='beto-data-v3', status='frozen_before_training_and_candidate_predictions',
        declared_at_utc=datetime.now(timezone.utc).isoformat(),
        hypothesis='El paquete de reparaciones v2 y v3, cuarentenas y 30 aportes de cinco obras puede mejorar la clasificación con una receta fija. Es una comparación del paquete completo; no separa sus componentes.',
        changes='Referencia original596 frente a copia v2 reparada596, luego nueve sustituciones/reclasificaciones y siete cuarentenas (589), más30 altas (619). Orden conservado entre supervivientes; altas anexadas en el orden aprobado.',
        training_dataset=DATASET, training_rows=619, training_rows_sha256=fingerprint(train),
        class_counts=dict(Counter(row['label'] for row in train)),
        original_class_counts=dict(Counter(row['label'] for row in original_train)),
        compared_with_original_train=dict(
            identity='Multiset of resourceId, exact text and label; ignores metadata and order.',
            unchanged=sum((original_identities & candidate_identities).values()),
            original_not_kept_exactly=sum((original_identities - candidate_identities).values()),
            candidate_new_or_changed=sum((candidate_identities - original_identities).values())),
        external_dataset=old['external_dataset'], external_content_sha256=external['content_sha256'],
        labels=old['labels'], metric_labels=old['metric_labels'],
        per_source_metric_labels=old['per_source_metric_labels'],
        baseline_report=PRIOR, baseline_prediction_field='per_item[].after',
        baseline_directory='outputs/beto-length-v1/run/candidate', baseline_rows=596,
        baseline_params=PARAMS, candidate_params=PARAMS, checkpoint_epoch=2,
        training_config=old['training_config'],
        fixed_recipe={**old['fixed_recipe'], 'microbatches_per_epoch': microbatches,
                      'last_accumulation_group_microbatches': microbatches % 8 or 8,
                      'schedule_total_steps': steps * 3, 'warmup_steps': max(1, int(steps * 3 * .1)),
                      'optimizer_update_attempts': steps * 2,
                      'why_not_epochs_2': 'Se ejecutan dos épocas manteniendo el horizonte de tres:117 pasos y11 warmup. Cambiar params.epochs a2 acortaría el horizonte a78 y warmup a7.',
                      'dataset_dependent_effects': '619 filas:310 microbatches,39 intentos/época,78 intentos totales, horizonte117; referencia596:298,38,76,114. Pesos de clase recalculados por la misma fórmula; no igualdad de actualizaciones efectivas garantizada por AMP.'},
        decision_rule=old['decision_rule'],
        evaluation_schedule='Reutilizar31 predicciones guardadas del modelo384; entrenar una sola configuración desde BETO base, guardar época2 y predecir una vez sobre esas mismas31 filas. No ajustar después.',
        resource_policy=dict(local_only=True, offline=True, modal=False, paid_services=False,
                             cuda_device=torch.cuda.get_device_name(), cuda_free_bytes=free, cuda_total_bytes=total,
                             on_failure='Record failure and stop; no automatic retry, CPU fallback or recipe change.'),
        packages=old['packages'], base_cache_files=old['base_cache_files'],
        input_guards=[guard(path) for path in dict.fromkeys(paths)],
        limits=[
            'Desarrollo externo reutilizado:31 párrafos revisados con IA,26 de Sala y5 de Sobrevilla; dos obras relacionadas y cinco clases. No es validación humana independiente ni test nuevo.',
            'Antecedentes coloniales y no_relevante no tienen soporte en este desarrollo; no se certifica el rendimiento de siete clases.',
            'La validación original81 procede de una fuente y ya se reutilizó. Aquí no se predice ni puntúa, ni tampoco test137.',
            'Una semilla y época fija; no prueba significación estadística ni identifica una causa única de éxito o fracaso.',
            'El paquete cambia textos, etiquetas, cantidad, orden efectivo, composición por fuente, pesos de clase y horizonte de pasos derivado. La corrección histórica no depende del signo de la métrica.',
            'Revisión de fuentes y duplicados reduce riesgos; no demuestra independencia completa entre obras, ediciones y documentos citados.',
            'No ejecutar otro ensayo ni sustituir producción automáticamente. Hace falta evaluación final independiente y cubrir todas las clases.',
            'Corpus completo y pesos permanecen locales; no se presupone permiso para redistribuir todas las fuentes.'
        ], training_started=False, candidate_predictions_started=False)
    protocol['content_sha256'] = fingerprint(protocol)
    check_protocol(protocol)
    PROTOCOL.parent.mkdir(parents=True, exist_ok=True)
    with PROTOCOL.open('x', encoding='utf-8', newline='\n') as stream:
        import json
        json.dump(protocol, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print('Frozen protocol:', sha(PROTOCOL), flush=True)


def run():
    require(not OUTPUT.exists(), 'Run directory exists; no automatic repeat')
    protocol_hash = sha(PROTOCOL)
    protocol = read(PROTOCOL)
    train, rows, before = check_protocol(protocol)
    import torch
    from beto_fixed_epoch import train_fixed_epoch
    from app.ml.beto_experiment import predict_beto
    require(torch.cuda.is_available(), 'CUDA required; no automatic CPU fallback')
    torch.set_num_threads(4)
    OUTPUT.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    stage = 'candidate_training'
    try:
        print('Training619, max_len384, fixed epoch2, scheduler horizon3; baseline reused', flush=True)
        details = train_fixed_epoch(train, protocol['labels'], PARAMS, protocol['training_config'],
                                    OUTPUT / 'candidate', checkpoint_epoch=2)
        write(OUTPUT / 'training-details.json', details)
        expected = dict(checkpoint_epoch=2, epochs_executed=2, schedule_epochs=3,
                        steps_per_epoch=39, schedule_total_steps=117, warmup_steps=11,
                        optimizer_update_attempts=78, checkpoint_saves=1, evaluation_rows_used=False,
                        predictions_performed=False, max_len=384, seed=42,
                        resolved_revision=protocol['training_config']['revision'])
        require(all(details[key] == value for key, value in expected.items()), 'Training differs from protocol')
        require(details['optimizer_updates'] + details['skipped_updates'] == 78
                and details['scheduler_steps'] == details['optimizer_updates']
                and len(details['history']) == 2
                and all(row['epoch'] == i and row['microbatches'] == 310
                        and row['optimizer_updates'] + row['skipped_updates'] == 39
                        for i, row in enumerate(details['history'], 1))
                and sum(row['optimizer_updates'] for row in details['history']) == details['optimizer_updates']
                and sum(row['skipped_updates'] for row in details['history']) == details['skipped_updates'],
                'Optimizer/scheduler/AMP counters differ')
        mapping = {str(i): label for i, label in enumerate(protocol['labels'])}
        require(read(OUTPUT / 'candidate/labels.json') == {'id2label': mapping, 'max_len': 384}, 'Candidate label map differs')
        require(read(OUTPUT / 'candidate/config.json')['id2label'] == mapping, 'Candidate model label map differs')
        stage = 'candidate_external_prediction'
        after = predict_beto(OUTPUT / 'candidate', rows, protocol['labels'], PARAMS)
        write(OUTPUT / 'candidate-external.json', dict(predictions=after))
        before_metrics = summarize(rows, before, protocol)
        after_metrics = summarize(rows, after, protocol)
        stage = 'final_integrity'
        check_protocol(protocol)
        require(sha(PROTOCOL) == protocol_hash, 'Protocol changed during execution')
        pairs = [dict(id=row['id'], source=row['resourceId'], truth=row['label'], text_sha256=row['text_sha256'],
                      before=a, after=b, before_correct=a == row['label'], after_correct=b == row['label'])
                 for row, a, b in zip(rows, before, after)]
        report = dict(schema_version=1, purpose='beto_data_v3_fixed_recipe_external_development',
                      created_at_utc=datetime.now(timezone.utc).isoformat(),
                      protocol=dict(path=PROTOCOL.relative_to(ROOT).as_posix(), sha256=protocol_hash,
                                    content_sha256=protocol['content_sha256']),
                      before=before_metrics, after=after_metrics, decision=decide(before_metrics, after_metrics),
                      per_item=pairs, training_details=details, training_configurations=1,
                      baseline_retrained=False, baseline_predictions_reused=True,
                      checkpoint_selected_on_new_predictions=False, old_validation_predictions_performed=False,
                      test_predictions_performed=False, production_changed=False, downloads_performed=False,
                      offline=True, inputs_unchanged=True, elapsed_seconds=round(time.perf_counter() - started, 2),
                      cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                      cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                      candidate_files=[guard(p.relative_to(ROOT).as_posix()) for p in sorted((OUTPUT / 'candidate').iterdir()) if p.is_file()],
                      limits=protocol['limits'])
        write(OUTPUT / 'report.json', report)
        print({key: report[key] for key in ['decision', 'elapsed_seconds']}, flush=True)
        return report
    except Exception as exc:
        write(OUTPUT / 'failure.json', dict(status='failed', stage=stage, error_type=type(exc).__name__,
                                           message=str(exc), elapsed_seconds=round(time.perf_counter() - started, 2),
                                           automatic_retry_or_recipe_change=False, production_changed=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'run'])
    action = parser.parse_args().action
    freeze() if action == 'freeze' else run()
