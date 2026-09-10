"""Apply explicitly adjudicated TRAIN-only changes in a separate snapshot."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256

from compare_beto_length import ROOT, read, sha, write
from compare_beto_loss_normalization import inputs as previous_inputs
from verify_external_development import fingerprint

ART = ROOT / 'artifacts/reviews/beto-training-cleanup-v1'
OUT = ROOT / 'outputs/corpus-snapshot-v4'
SOURCE = ROOT / 'outputs/corpus-snapshot-v3/reviewed-export.json'
DECISIONS = ART / 'adjudication.json'


def guard(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path))


def build():
    assert not OUT.exists(), 'Never overwrite a snapshot'
    prior, _, _ = previous_inputs()
    decisions = read(DECISIONS)
    review = read(ROOT / 'artifacts/reviews/independent-review-v1/training-review.json')
    reviewed = {r['snapshot_index']: r for r in review['items']}
    source = read(SOURCE)
    items = source['items']
    actions = {r['snapshot_index']: r for r in decisions['items']}
    assert len(actions) == len(decisions['items']) == 8
    assert set(actions) == {49, 127, 194, 242, 577, 643, 675, 697}
    kept, archive, mapping = [], [], []
    for index, row in enumerate(items):
        candidate = deepcopy(row)
        if index in actions:
            action = actions[index]
            assert row['split'] == 'train'
            assert action['text_sha256'] == reviewed[index]['text_sha256'] == sha256(row['text'].encode('utf-8')).hexdigest()
            assert action['before_label'] == row['label']
            assert action['reason'] and action['action'] in ('keep', 'quarantine', 'relabel')
            if action['action'] == 'quarantine':
                assert action['after_label'] is None
                archive.append(dict(snapshot_index=index, original=row, decision=action))
                continue
            if action['action'] == 'relabel':
                assert index == 49 and action['after_label'] == 'no_relevante'
                candidate['label'] = action['after_label']
                archive.append(dict(snapshot_index=index, original=row, decision=action))
            else:
                assert action['after_label'] == row['label']
        mapping.append(dict(parent_snapshot_index=index, candidate_snapshot_index=len(kept)))
        kept.append(candidate)
    old_train = [(i, r) for i, r in enumerate(items) if r['split'] == 'train']
    candidate = dict(source, dataset='experimental-training-cleanup-v4', items=kept)
    train = [r for r in kept if r['split'] == 'train']
    quarantined = [i for i, a in actions.items() if a['action'] == 'quarantine']
    assert len(train) == 619 - len(quarantined)
    assert set(r['label'] for r in train) == set(source['labels'])
    assert [r for r in kept if r['split'] != 'train'] == [r for r in items if r['split'] != 'train']
    expected_indices = [i for i in range(len(items)) if i not in quarantined]
    assert [m['parent_snapshot_index'] for m in mapping] == expected_indices
    for original_index, row in zip(expected_indices, kept):
        expected = dict(items[original_index])
        if original_index == 49:
            expected['label'] = 'no_relevante'
        assert row == expected, original_index
    assert len(set(r['resourceId'] for r in train)) == 14
    preserved = {g['path']: g for g in prior['input_guards']}
    for path in (SOURCE, DECISIONS, ART / 'context-review.json', ROOT / 'scripts/build_beto_training_cleanup.py',
                 ROOT / 'artifacts/experiments/beto-loss-normalization-v1/protocol.json',
                 ROOT / 'artifacts/experiments/beto-loss-normalization-v1/report.json',
                 ROOT / 'artifacts/experiments/beto-loss-normalization-v1/verification.json'):
        preserved[path.relative_to(ROOT).as_posix()] = guard(path)
    context = read(ART / 'context-review.json')
    for entry in context['sources']:
        path = ROOT / entry['pdf_path']
        assert sha(path) == entry['pdf_sha256']
        preserved[entry['pdf_path']] = guard(path)
    for entry in context['page_evidence']:
        path = ROOT / entry['text_path']
        assert sha(path) == entry['text_sha256']
        preserved[entry['text_path']] = guard(path)
        if entry['image_path']:
            path = ROOT / entry['image_path']
            preserved[entry['image_path']] = guard(path)
    OUT.mkdir(parents=True)
    write(OUT / 'reviewed-export.json', candidate)
    write(OUT / 'originals-and-decisions.json', dict(items=archive))
    write(OUT / 'row-mapping.json', dict(items=mapping))
    report = dict(status='applied_to_separate_experimental_snapshot_ai_review',
        source=guard(SOURCE), dataset=guard(OUT / 'reviewed-export.json'), decisions=guard(DECISIONS),
        train_before=len(old_train), train_after=len(train), quarantine_snapshot_indices=sorted(quarantined),
        relabeled_snapshot_indices=[49], unchanged_original_rows=len(items)-len(quarantined)-1,
        text_edits=0, validation_rows=81, test_rows=137, evaluation_rows_identical=True,
        training_rows_sha256=fingerprint(train), evaluation_sha256=fingerprint([r for r in items if r['split'] != 'train']),
        counts_before=dict(Counter(r['label'] for _, r in old_train)), counts_after=dict(Counter(r['label'] for r in train)),
        sources=14, input_guards=list(preserved.values()),
        limits=['Eight selected units adjudicated, not a full-corpus quality certification.',
                'IA review; no independent human gold. Quarantine is not a new class.',
                'No new evaluation examples moved into training. No performance claim.'])
    write(ART / 'build-report.json', report)
    for entry in preserved.values():
        assert sha(ROOT / entry['path']) == entry['sha256'], entry['path']
    write(ART / 'build-verification.json', dict(status='passed', exact_rows_checked=len(kept),
        original_rows_archived=len(archive), held_evaluation_identical=218,
        all_seven_classes=True, sources_unchanged=14, text_edits=0,
        guarded_inputs=len(preserved), dataset_sha256=sha(OUT / 'reviewed-export.json')))
    print(report['train_before'], '->', report['train_after'], 'TRAIN; quarantine', sorted(quarantined))


if __name__ == '__main__':
    build()
