"""TRAIN coverage audit and one bounded real-BETO memorization diagnostic."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256

from compare_beto_length import ROOT, read, sha, write
from compare_beto_training_cleanup import inputs as previous_inputs
from compare_beto_source_epochs import now
from compare_beto_loss_normalization import guard
from compare_tfidf_beto_work_control import score
from verify_external_development import fingerprint

ART = ROOT / 'artifacts/experiments/beto-learning-sanity-v1'
OUT = ROOT / 'outputs/beto-learning-sanity-v1'
AUDIT = ROOT / 'artifacts/reviews/beto-root-cause-v1'
DATA = ROOT / 'outputs/corpus-snapshot-v4/reviewed-export.json'


def freeze():
    assert not ART.exists() and not OUT.exists() and not AUDIT.exists()
    previous, _, _ = previous_inputs()
    data = read(DATA)
    indexed = [(i, r) for i, r in enumerate(data['items']) if r['split'] == 'train']
    labels = data['labels']
    from transformers import AutoTokenizer
    cfg = previous['training_config']
    tokenizer = AutoTokenizer.from_pretrained(cfg['base_model'], revision=cfg['revision'], local_files_only=True)
    encoded = tokenizer([r['text'] for _, r in indexed], truncation=False, padding=False)['input_ids']
    actual = tokenizer([r['text'] for _, r in indexed], truncation=True, max_length=384, padding=False)['input_ids']
    assert len(indexed) == 613
    by_class, by_source, inputs = defaultdict(Counter), defaultdict(Counter), defaultdict(list)
    row_info = []
    for train_index, ((si, row), tokens, truncated) in enumerate(zip(indexed, encoded, actual)):
        by_class[row['label']][row['resourceId']] += 1
        by_source[row['resourceId']][row['label']] += 1
        key = fingerprint(truncated)
        inputs[key].append((si, row['label']))
        row_info.append(dict(snapshot_index=si, train_index=train_index, label=row['label'], source=row['resourceId'],
            text_sha256=sha256(row['text'].encode('utf-8')).hexdigest(), tokens=len(tokens), words=len(row['text'].split()),
            truncated_at384=len(tokens)>384, model_input_sha256=key))
    collisions = [dict(input_sha256=key, rows=rows, conflicting_labels=len({label for _,label in rows})>1)
        for key,rows in inputs.items() if len(rows)>1]
    upper_bound = sum(max(Counter(label for _,label in rows).values()) for rows in inputs.values())
    summaries = {}
    for label in labels:
        counts = by_class[label]
        total = sum(counts.values())
        subset = [r for r in row_info if r['label']==label]
        summaries[label] = dict(rows=total, sources=len(counts), sources_with_at_least5=sum(v>=5 for v in counts.values()),
            source_counts=dict(counts), largest_source=counts.most_common(1)[0][0], largest_source_rows=max(counts.values()),
            largest_share=max(counts.values())/total, top3_share=sum(v for _,v in counts.most_common(3))/total,
            concentration_equivalent_sources=1/sum((n/total)**2 for n in counts.values()),
            truncated_at384=sum(r['truncated_at384'] for r in subset))
    # LOO descriptive metadata-only baseline, not an unseen-source prediction test.
    source_only, global_only = [], []
    global_counts = Counter(r['label'] for _,r in indexed)
    for _,row in indexed:
        local = by_source[row['resourceId']].copy()
        local[row['label']] -= 1
        all_other = global_counts.copy()
        all_other[row['label']] -= 1
        winner = lambda counts: max(labels, key=lambda label:(counts[label], -labels.index(label)))
        source_only.append(winner(local) if sum(local.values()) else winner(all_other))
        global_only.append(winner(all_other))
    rows = [r for _,r in indexed]
    selected = []
    for label in labels:
        eligible = [r for r in row_info if r['label']==label and r['tokens']<=384 and 120<=r['words']<=250
                    and data['items'][r['snapshot_index']]['sourceType']=='pdf'
                    and len(inputs[r['model_input_sha256']])==1]
        eligible.sort(key=lambda r:r['text_sha256'])
        chosen, seen_sources = [], set()
        for row in eligible:
            if row['source'] not in seen_sources and len(chosen)<4:
                chosen.append(row)
                seen_sources.add(row['source'])
        for row in eligible:
            if row not in chosen and len(chosen)<4:
                chosen.append(row)
        assert len(chosen)==4, label
        selected.extend(chosen)
    selected.sort(key=lambda r:r['snapshot_index'])
    assert len(selected)==28 and len({r['model_input_sha256'] for r in selected})==28
    params = dict(previous['params'], epochs=50)
    guards = {g['path']:g for g in previous['input_guards']}
    for path in (DATA, ROOT / 'scripts/diagnose_beto_learning_sanity.py',
                 ROOT / 'artifacts/experiments/beto-training-cleanup-v1/report.json',
                 ROOT / 'artifacts/experiments/beto-training-cleanup-v1/verification.json'):
        guards[path.relative_to(ROOT).as_posix()] = guard(path)
    audit = dict(status='descriptive_TRAIN_only_not_causal_proof', dataset=guard(DATA), rows=613,
        class_summary=summaries, source_class_counts={k:dict(v) for k,v in by_source.items()},
        exact_model_input_collisions=collisions, maximum_correct_given_input_collisions=upper_bound,
        row_diagnostics=row_info, source_only_leave_one_out=score(rows,source_only,list(range(613)),labels),
        global_only_leave_one_out=score(rows,global_only,list(range(613)),labels),
        limits=['Source association does not prove BETO uses source shortcuts.',
                'resourceId counts are not independent-work counts; related works can share evidence.',
                'Concentration-equivalent sources is inverse squared share, not a statistical effective sample size.',
                'Metadata-only LOO uses other labels from the same source; not legitimate unseen-source evaluation.',
                'Token truncation counts are descriptive, not an estimate of its causal harm.'])
    p = dict(status='frozen_before_real_BETO_training', created_at_utc=now(), dataset=guard(DATA),
        question='Can the real pinned BETO and existing optimizer learn28 repeated distinct TRAIN inputs across all7labels?',
        selected=selected, labels=labels, params=params, training_config=cfg,
        checkpoint_epochs=[50], maximum_update_attempts=100, input_guards=list(guards.values()),
        selection='Four per class, unique model inputs, PDF120-250words fitting384tokens, SHA ordering with source diversity first; no model predictions used.',
        success='At epoch50: exactly28/28 correct and all seven class recalls1.0 on these SAME inputs. No intermediate inference or adaptive extension.',
        failure_interpretation='Failure does not prove a broken model; inspect optimization, selected inputs, loss and updates before extending.',
        success_interpretation='Only rules against gross inability to fit this small set under this longer diagnostic budget. Memorization can include mistaken labels; does not validate labels or generalization.',
        changes_from_work_holdout='Tiny balanced subset repeated50epochs with scheduler horizon50: diagnostic, not candidate comparison or recommendation to use50epochs on whole corpus.',
        stop='One fresh local trajectory, one snapshot,28in-sample predictions; no pilot, validation, test, external or full-corpus evaluation. No production promotion.')
    p['content_sha256'] = fingerprint(p)
    ART.mkdir(parents=True)
    AUDIT.mkdir(parents=True)
    write(AUDIT / 'quantitative-coverage.json', audit)
    write(ART / 'protocol.json', p)
    print('Frozen28 inputs,4per class,50epochs,100update attempts.', flush=True)
    print('Truncated',sum(r['truncated_at384'] for r in row_info),'input collision bound',upper_bound, flush=True)


def inputs():
    p = read(ART / 'protocol.json')
    assert p['content_sha256']==fingerprint({k:v for k,v in p.items() if k!='content_sha256'})
    for g in p['input_guards']:
        assert sha(ROOT/g['path'])==g['sha256'],g['path']
    data = read(DATA)
    rows=[]
    for entry in p['selected']:
        row=data['items'][entry['snapshot_index']]
        assert row['split']=='train' and row['label']==entry['label']
        assert sha256(row['text'].encode('utf-8')).hexdigest()==entry['text_sha256']
        rows.append(row)
    assert Counter(r['label'] for r in rows)==Counter({label:4 for label in p['labels']})
    return p,rows


def run():
    p,rows=inputs()
    assert not OUT.exists()
    from beto_effective_batch_loss import train_epoch_trajectory
    from app.ml.beto_experiment import predict_beto
    d=train_epoch_trajectory(rows,p['labels'],p['params'],p['training_config'],OUT,(50,))
    write(OUT/'training-details.json',d)
    predicted=predict_beto(OUT/'epoch-50',rows,p['labels'],p['params'])
    m=score(rows,predicted,list(range(28)),p['labels'])
    records=[dict(**entry,truth=row['label'],predicted=pred) for entry,row,pred in zip(p['selected'],rows,predicted)]
    write(OUT/'predictions.json',dict(items=records))
    inputs()
    report=dict(protocol=guard(ART/'protocol.json'),metrics=m,training_details=d,
        result='small_set_memorization_passed_not_generalization' if m['correct']==28 else 'small_set_memorization_not_passed_in_fixed_budget',
        predictions_role='training_same28_not_validation',selected_model=None,
        output_guards=[guard(path) for path in sorted(OUT.rglob('*')) if path.is_file()])
    write(ART/'report.json',report)
    print(report['result'],m['correct'],'/28',flush=True)


def verify():
    from sklearn.metrics import confusion_matrix,f1_score
    p,rows=inputs()
    report=read(ART/'report.json')
    assert report['protocol']==guard(ART/'protocol.json')
    for g in report['output_guards']:
        assert sha(ROOT/g['path'])==g['sha256']
    records=read(OUT/'predictions.json')['items']
    assert len(records)==28
    for selected,row,entry in zip(p['selected'],rows,records):
        assert all(entry[k]==v for k,v in selected.items()) and entry['truth']==row['label']
        assert entry['predicted'] in p['labels']
    truth=[r['label'] for r in rows]
    pred=[r['predicted'] for r in records]
    m=report['metrics']
    assert confusion_matrix(truth,pred,labels=p['labels']).tolist()==m['confusion_matrix']
    assert sum(a==b for a,b in zip(truth,pred))==m['correct']
    assert abs(f1_score(truth,pred,labels=p['labels'],average='macro',zero_division=0)-m['f1_macro_all_seven'])<1e-12
    d=read(OUT/'training-details.json')
    assert d==report['training_details'] and d['epochs_executed']==50 and d['checkpoint_saves']==1
    assert d['optimizer_update_attempts']==100==d['optimizer_updates']+d['skipped_updates']
    assert d['scheduler_steps']==d['optimizer_updates'] and d['schedule_total_steps']==100 and d['warmup_steps']==10
    assert all(v==1.0 for v in d['class_weights'].values())
    assert all(v==4 for v in d['class_counts'].values())
    assert d['loss_normalization']=='weighted_CE_sum_per_microbatch_divided_by_target_weight_sum_of_actual_accumulation_group'
    assert report['result']==('small_set_memorization_passed_not_generalization' if m['correct']==28 else 'small_set_memorization_not_passed_in_fixed_budget')
    write(ART/'verification.json',dict(status='passed',prediction_rows=28,all_seven_labels_checked=True,
        updates=d['optimizer_updates'],skipped=d['skipped_updates'],guarded_inputs=len(p['input_guards']),
        output_files_checked=len(report['output_guards']),report_sha256=sha(ART/'report.json'),
        limitation='Verified training-set diagnostic, not a validation score.'))
    print('Verified',m['correct'],'/28',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','run','verify'))
    globals()[parser.parse_args().action]()
