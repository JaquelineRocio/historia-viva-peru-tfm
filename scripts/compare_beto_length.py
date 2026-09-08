"""One offline length comparison at a fixed epoch, on frozen external development."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'apps/ml'))
from verify_external_development import fingerprint, verify, workspace_file


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8'))


def metric_report(truth, predicted, labels, metric_labels):
    if not truth or len(truth) != len(predicted):
        raise ValueError('Nonempty aligned predictions required')
    if len(set(labels)) != len(labels) or not set(truth+predicted) <= set(labels):
        raise ValueError('Unknown or repeated label')
    if metric_labels != [label for label in labels if label in set(truth)]:
        raise ValueError('Macro labels must match declared support in taxonomy order')
    matrix = [[0]*len(labels) for _ in labels]
    positions = {label:i for i,label in enumerate(labels)}
    for actual, guess in zip(truth, predicted):
        matrix[positions[actual]][positions[guess]] += 1
    per_class = []
    for i,label in enumerate(labels):
        tp = matrix[i][i]
        support = sum(matrix[i])
        guesses = sum(row[i] for row in matrix)
        per_class.append(dict(label=label, support=support, predicted_count=guesses,
                              precision=tp/guesses if guesses else 0.0,
                              recall=tp/support if support else 0.0,
                              f1=2*tp/(support+guesses) if support+guesses else 0.0))
    correct = sum(matrix[i][i] for i in range(len(labels)))
    absent = [row for row in per_class if row['support']==0]
    return dict(rows=len(truth), correct=correct, accuracy=correct/len(truth),
                f1_macro=sum(row['f1'] for row in per_class if row['label'] in metric_labels)/len(metric_labels),
                metric_labels=metric_labels, labels=labels, confusion_matrix=matrix,
                per_class=per_class,
                predictions_to_unassessed_labels={row['label']:row['predicted_count'] for row in absent})


def summarize(rows, predictions, protocol):
    labels=protocol['labels']
    if set(protocol['per_source_metric_labels'])!={row['resourceId'] for row in rows}:
        raise ValueError('Per-source protocol must cover exactly all evaluation works')
    metrics=metric_report([row['label'] for row in rows],predictions,labels,protocol['metric_labels'])
    metrics['per_source']={}
    for source, present in protocol['per_source_metric_labels'].items():
        indices=[i for i,row in enumerate(rows) if row['resourceId']==source]
        metrics['per_source'][source]=metric_report([rows[i]['label'] for i in indices],
                                                   [predictions[i] for i in indices],labels,present)
    return metrics


def decide(before, after):
    def support(value):
        return value['rows'], value['labels'], value['metric_labels'], [(r['label'],r['support']) for r in value['per_class']]
    if (support(before)!=support(after) or not before['per_source']
            or set(before['per_source'])!=set(after['per_source'])
            or any(support(value)!=support(after['per_source'][source])
                   for source,value in before['per_source'].items())):
        raise ValueError('Decision requires identical global and per-work support')
    delta=after['f1_macro']-before['f1_macro']
    total_ok=after['correct']>=before['correct']
    source_ok=all(after['per_source'][source]['correct']>=value['correct']
                  for source,value in before['per_source'].items())
    favorable=delta>0 and total_ok and source_ok
    status='favorable_exploratory_signal' if favorable else ('mixed_signal' if delta>0 else 'no_positive_signal')
    return dict(status=status, delta_f1_macro=delta, delta_correct=after['correct']-before['correct'],
                total_correct_not_lower=total_ok, no_source_correct_count_lower=source_ok,
                candidate_selected_for_production=False,
                reason='Predeclared: macro increases, total correct does not fall and neither work loses correct predictions; still partial exploratory evidence only.')


def check_protocol(protocol):
    body={k:v for k,v in protocol.items() if k!='content_sha256'}
    if protocol.get('content_sha256')!=fingerprint(body) or protocol.get('status')!='frozen_before_predictions':
        raise ValueError('Protocol is not frozen with matching hash')
    expected={'lr':2e-5,'epochs':3,'batch_size':2,'gradient_accumulation_steps':8,'max_len':384}
    if protocol['candidate_params'] != expected or protocol['checkpoint_epoch']!=2:
        raise ValueError('Only the declared length comparison is supported')
    if protocol['baseline_params']!={**expected,'max_len':192}:
        raise ValueError('Baseline recipe mismatch')
    if protocol['training_config']!={'base_model':'dccuchile/bert-base-spanish-wwm-cased',
                                     'revision':'c4d86612f51b4f46759c8390d1798c2febe71b93','seed':42}:
        raise ValueError('Base model/revision/seed mismatch')
    for entry in protocol['input_guards']:
        if sha(workspace_file(entry['path']))!=entry['sha256']:
            raise ValueError('Changed input: '+entry['path'])
    for package, version in protocol['packages'].items():
        if importlib.metadata.version(package)!=version:
            raise ValueError('Changed package: '+package)
    from huggingface_hub.constants import HF_HUB_CACHE
    config=protocol['training_config']
    cached=Path(HF_HUB_CACHE)/('models--'+config['base_model'].replace('/','--'))/'snapshots'/config['revision']
    for entry in protocol['base_cache_files']:
        if Path(entry['name']).name!=entry['name'] or sha(cached/entry['name'])!=entry['file_sha256']:
            raise ValueError('Changed pinned base cache')


def run(protocol_path, output):
    output=Path(output).resolve()
    if output.exists() or not output.is_relative_to((ROOT/'outputs').resolve()):
        raise ValueError('Use a new output directory inside outputs')
    protocol_file_hash=sha(protocol_path)
    protocol=read(protocol_path)
    check_protocol(protocol)
    external=read(workspace_file(protocol['external_dataset']))
    verify(external,check_local_inputs=True)
    if external['content_sha256']!=protocol['external_content_sha256']:
        raise ValueError('Changed external development')
    reference=read(workspace_file(protocol['training_dataset']))
    train=[row for row in reference['items'] if row['split']=='train']
    if len(train)!=596 or fingerprint(train)!=protocol['training_rows_sha256']:
        raise ValueError('Training membership/order differs')
    rows=external['items']
    if (reference['labels']!=external['labels'] or external['metric_labels']!=protocol['metric_labels']
            or external['labels']!=protocol['labels']):
        raise ValueError('Taxonomy or macro support differs')
    expected_sources={source:[label for label in external['labels']
                     if any(row['resourceId']==source and row['label']==label for row in rows)]
                     for source in external['source_counts']}
    if protocol['per_source_metric_labels']!=expected_sources:
        raise ValueError('Declared per-source support differs before prediction')
    # Evaluation rows never reach the trainer. Old val/test have no inference path here.
    del reference
    baseline=ROOT/protocol['baseline_directory']
    labels=protocol['labels']
    mapping={str(i):label for i,label in enumerate(labels)}
    if read(baseline/'labels.json')!={'id2label':mapping,'max_len':192}:
        raise ValueError('Baseline label order/max_len differs')
    if read(baseline/'config.json')['id2label']!=mapping:
        raise ValueError('Baseline model label map differs')
    import torch
    from app.ml.beto_experiment import predict_beto
    from beto_fixed_epoch import train_fixed_epoch
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA required; no automatic CPU or batch-size fallback')
    torch.set_num_threads(4)
    output.mkdir(parents=True,exist_ok=False)
    torch.cuda.reset_peak_memory_stats()
    started=time.perf_counter()
    stage='baseline_external_prediction'
    try:
        print('Predicting frozen external development with reference192',flush=True)
        before=predict_beto(baseline,rows,labels,protocol['baseline_params'])
        before_metrics=summarize(rows,before,protocol)
        write(output/'baseline-external.json',dict(metrics=before_metrics,predictions=before))
        stage='candidate_training'
        print('Training384: fixed epoch2; scheduler horizon3; no validation selection',flush=True)
        details=train_fixed_epoch(train,labels,protocol['candidate_params'],protocol['training_config'],
                                  output/'candidate',checkpoint_epoch=protocol['checkpoint_epoch'])
        if (details['resolved_revision']!=protocol['training_config']['revision']
                or details['checkpoint_epoch']!=2 or details['epochs_executed']!=2
                or details['schedule_epochs']!=3 or details['schedule_total_steps']!=114
                or details['warmup_steps']!=11 or details['optimizer_update_attempts']!=76
                or details['evaluation_rows_used'] is not False or details['checkpoint_saves']!=1):
            raise ValueError('Executed training differs from fixed-epoch protocol')
        stage='candidate_external_prediction'
        after=predict_beto(output/'candidate',rows,labels,protocol['candidate_params'])
        after_metrics=summarize(rows,after,protocol)
        if read(output/'candidate'/'labels.json')!={'id2label':mapping,'max_len':384}:
            raise ValueError('Saved candidate mapping/max_len differs')
        stage='final_integrity'
        check_protocol(protocol)
        if sha(protocol_path)!=protocol_file_hash:
            raise ValueError('Protocol file changed during execution')
        per_item=[dict(id=row['id'],source=row['resourceId'],truth=row['label'],
                       text_sha256=row['text_sha256'],before=a,after=b,
                       before_correct=a==row['label'],after_correct=b==row['label'])
                  for row,a,b in zip(rows,before,after)]
        report=dict(schema_version=1,purpose='beto_length_fixed_epoch_external_development',
                    created_at_utc=datetime.now(timezone.utc).isoformat(),
                    protocol=dict(path=protocol_path.relative_to(ROOT).as_posix(),sha256=sha(protocol_path),
                                  content_sha256=protocol['content_sha256']),
                    before=before_metrics,after=after_metrics,decision=decide(before_metrics,after_metrics),
                    per_item=per_item,training_details=details,training_configurations=1,
                    baseline_retrained=False,checkpoint_selected_on_new_predictions=False,
                    old_validation_predictions_performed=False,test_predictions_performed=False,
                    production_changed=False,downloads_performed=False,offline=True,
                    inputs_unchanged=True,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                    working_tree_dirty=bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip()),
                    elapsed_seconds=round(time.perf_counter()-started,2),
                    cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                    candidate_files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
                                     for p in sorted((output/'candidate').iterdir()) if p.is_file()],
                    limits=protocol['limits'])
        write(output/'report.json',report)
        print(json.dumps(dict(before_f1=before_metrics['f1_macro'],after_f1=after_metrics['f1_macro'],
                              before_correct=before_metrics['correct'],after_correct=after_metrics['correct'],
                              decision=report['decision']['status']),ensure_ascii=False),flush=True)
        return report
    except Exception as exc:
        write(output/'failure.json',dict(status='failed',stage=stage,error_type=type(exc).__name__,
              message=str(exc),elapsed_seconds=round(time.perf_counter()-started,2),
              old_validation_predictions_performed=False,test_predictions_performed=False,
              production_changed=False,automatic_retry_or_recipe_change=False))
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    target=args.output.resolve()
    if target.exists() or not target.is_relative_to((ROOT/'outputs').resolve()):
        parser.error('Use a new directory inside outputs; no overwrite')
    run(args.protocol.resolve(),target)


if __name__=='__main__':
    main()
