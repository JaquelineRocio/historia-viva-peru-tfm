"""Select twelve TRAIN contrasts and expose exact token windows; no model calls."""
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'apps/ml')]
from compare_beto_length import read, sha, write
from verify_external_development import fingerprint

OUT = ROOT / 'outputs/beto-ideas-contrast-v1'
SELECTION = ROOT / 'artifacts/reviews/beto-ideas-contrast-v1-selection.json'
IDEAS = 'crisis_ideas_emancipadoras'
STOP = set('para como este esta estos estas entre sobre desde hasta porque donde cuando aunque tambien solo todo todos todas cada mismo misma siendo fueron habia tiene tienen puede pueden ellos ellas nosotros nuestro nuestra pero sino otra otro otras otros entonces mientras ademas parte forma manera hacer haber estar sido'.split())


def words(text):
    value = unicodedata.normalize('NFKD', text.casefold()).replace('\u00ad', '')
    value = ''.join(c for c in value if not unicodedata.combining(c))
    return {w for w in re.findall(r'\w+', value) if len(w) >= 4 and w not in STOP}


def main():
    resume = sys.argv[1:] == ['--resume-selection']
    if SELECTION.exists() or (OUT.exists() and not resume):
        raise ValueError('Selection exists; no repeat/overwrite')
    if resume:
        assert not (OUT / 'passages.json').exists()
        initial = read(OUT / 'selection-initial.json')
        assert initial['content_sha256'] == fingerprint({k: v for k, v in initial.items() if k != 'content_sha256'})
        original_script_hash = next(e['sha256'] for e in initial['input_guards']
                                    if e['path'] == 'scripts/prepare_beto_ideas_contrast.py')
        assert sha(OUT / 'prepare-initial.py') == original_script_hash
    parent_path = ROOT / 'artifacts/experiments/beto-source-epochs-v1/protocol.json'
    parent, report = read(parent_path), read(parent_path.parent / 'report.json')
    assert report['protocol']['sha256'] == sha(parent_path)
    guards = {e['path']: e for e in parent['input_guards'] + report['checkpoint_files'] + report['prediction_files']}
    for path in ['scripts/prepare_beto_ideas_contrast.py', 'docs/guia-etiquetado-1780-1842.md',
                 'artifacts/experiments/beto-source-epochs-v1/protocol.json',
                 'artifacts/experiments/beto-source-epochs-v1/report.json',
                 'artifacts/experiments/beto-source-epochs-v1/verification.json']:
        guards[path] = dict(path=path, sha256=sha(ROOT / path))
    for e in guards.values():
        assert sha(ROOT / e['path']) == e['sha256'], e['path']
    data = read(ROOT / parent['dataset'])
    indexed = [(i, r) for i, r in enumerate(data['items']) if r['split'] == 'train']
    rows = [r for _, r in indexed]
    assert fingerprint(rows) == parent['training_rows_sha256'] and len(rows) == 619
    labels = data['labels']
    del data
    tokens = [words(r['text']) for r in rows]
    def key(i):
        return hashlib.sha256(('42|' + rows[i]['resourceId'] + '|' + rows[i]['text']).encode('utf-8')).hexdigest(), i
    def score(i, j):
        return len(tokens[i] & tokens[j]) / len(tokens[i] | tokens[j]) if tokens[i] | tokens[j] else 0.
    predictions, errors = {}, []
    for fold in parent['folds']:
        name = fold['id']
        records = read(ROOT / 'outputs/beto-source-epochs-v1' / name / 'epoch-2-predictions.json')['items']
        assert len(records) == len(rows)
        for i, p in enumerate(records):
            assert p['train_index'] == i and p['snapshot_index'] == indexed[i][0]
            assert p['truth'] == rows[i]['label'] and p['source'] == rows[i]['resourceId']
            assert p['text_sha256'] == hashlib.sha256(rows[i]['text'].encode()).hexdigest()
        predictions[name] = records
        pool = [i for i in fold['primary_indices'] if rows[i]['label'] == IDEAS and records[i]['predicted'] != IDEAS]
        counts = Counter(records[i]['predicted'] for i in pool)
        strata = sorted(counts, key=lambda label: (-counts[label], labels.index(label)))[:2]
        for label in strata:
            candidates = [i for i in pool if records[i]['predicted'] == label]
            errors.append(dict(fold=name, index=min(candidates, key=key), confused_label=label,
                               stratum_size=len(candidates), full_error_class_counts=dict(counts)))
    used = {e['index'] for e in errors}
    assert len(used) == 4
    triplets = []
    for n, error in enumerate(errors, 1):
        fold = next(f for f in parent['folds'] if f['id'] == error['fold'])
        records = predictions[fold['id']]
        members = []
        for role, label in [('error', IDEAS), ('ideas_correct_fit', IDEAS), ('confused_class_correct_fit', error['confused_label'])]:
            if role == 'error':
                i, eligible = error['index'], error['stratum_size']
            else:
                pool = [j for j in fold['fit_indices'] if j not in used and rows[j]['label'] == label
                        and records[j]['predicted'] == label]
                assert pool
                i, eligible = min(pool, key=lambda j: (-score(error['index'], j), key(j))), len(pool)
                used.add(i)
            members.append(dict(id=f'T{n}-{role}', role=role, train_index=i, snapshot_index=indexed[i][0],
                source=rows[i]['resourceId'], label=rows[i]['label'], predicted=records[i]['predicted'],
                text_sha256=records[i]['text_sha256'], eligible_pool=eligible,
                lexical_jaccard_to_error=score(error['index'], i)))
        triplets.append(dict(id=f'T{n}', fold=fold['id'], error_strata=error['full_error_class_counts'], members=members))
    assert len(used) == 12
    if resume:
        assert triplets == initial['triplets'], 'Recovery must not change sample membership or roles'
    selection = dict(schema_version=1, id='beto-ideas-contrast-v1', status='frozen_before_reading_selected_passages',
        created_at_utc=datetime.now(timezone.utc).isoformat(), epoch_used=2, triplets=triplets,
        question='For these twelve passages, are class boundaries consistent, does the384-token input contain the decisive argument, and what comparable fit examples exist?',
        selection_rule='Per primary work: two most frequent epoch2 ideas error destinations; one error per destination by SHA256(42|source|text), tie train index. Then one correctly predicted fit ideas and one correctly predicted fit destination-class example per error: highest lexical Jaccard, tie same hash. Exclude all four errors and previously selected controls; twelve distinct rows.',
        lexical_rule='NFKD casefold, remove accents/soft hyphen, word set length>=4 excluding STOP in guarded script. Mechanical retrieval only, not semantic equivalence or coverage proof.',
        limits=['Selected using stored labels/predictions, not blind or representative; no annotation error rate estimate.',
                'AI review, not independent human historical adjudication. Prediction correctness means agreement with stored label only.',
                'Nearest lexical controls do not establish semantic absence across all TRAIN. Distinguish examples found from unknown coverage.',
                'Existing historical reviews are reused and may concern other snapshot text; exact hashes must match.',
                'No data/label change, classifier fitting, model inference, external31/old validation/test analysis or paid services.'],
        input_guards=list(guards.values()))
    if resume:
        selection['serialization_recovery'] = dict(
            initial_selection_sha256=sha(OUT / 'selection-initial.json'),
            original_script_sha256=sha(OUT / 'prepare-initial.py'),
            membership_and_roles_unchanged=True,
            reason='BatchEncoding was not JSON serializable; convert to plain dict. No new sample, model load or prediction.')
    selection['content_sha256'] = fingerprint(selection)
    write(SELECTION, selection)
    OUT.mkdir(parents=True, exist_ok=resume)
    from transformers import AutoTokenizer
    tokenizer_path = ROOT / 'outputs/beto-data-v3/run/candidate'
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    assert tokenizer.truncation_side == 'right' and tokenizer.is_fast
    passages = []
    selected_rows = []
    for triplet in triplets:
        for member in triplet['members']:
            row = rows[member['train_index']]
            full = tokenizer(row['text'], truncation=False, add_special_tokens=True)
            visible = tokenizer(row['text'], truncation=True, max_length=384, padding='max_length', return_offsets_mapping=True)
            boundary = max(end for start, end in visible.pop('offset_mapping'))
            passages.append(dict(**member, triplet=triplet['id'], fold=triplet['fold'], text=row['text'],
                visible_text=row['text'][:boundary], omitted_text=row['text'][boundary:], visible_char_end=boundary,
                full_tokens=len(full['input_ids']), kept_tokens=sum(visible['attention_mask']), model_inputs=dict(visible)))
            selected_rows.append(row)
    # Verify exact equality against the shared classifier loader, not a decoded approximation.
    from app.ml.beto_experiment import _loader
    loader, keys = _loader(selected_rows, tokenizer, labels, dict(batch_size=2, max_len=384))
    for k, tensor in zip(keys, loader.dataset.tensors[:-1]):
        assert tensor.tolist() == [p['model_inputs'][k] for p in passages]
    write(OUT / 'passages.json', dict(items=passages))
    for e in guards.values():
        assert sha(ROOT / e['path']) == e['sha256']
    write(OUT / 'preparation-check.json', dict(status='passed', rows=12, distinct_rows=12,
        selection_sha256=sha(SELECTION), passages_sha256=sha(OUT / 'passages.json'), exact_loader_inputs_equal=True,
        protected_files=len(guards), training_performed=False, model_predictions_performed=False))
    print(json.dumps([dict(id=p['id'], snapshot_index=p['snapshot_index'], source=p['source'],
                          label=p['label'], predicted=p['predicted'], full_tokens=p['full_tokens']) for p in passages]))


if __name__ == '__main__':
    main()
