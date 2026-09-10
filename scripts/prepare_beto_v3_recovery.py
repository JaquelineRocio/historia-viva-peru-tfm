"""Freeze authentic V recovery candidates; never annotate or admit references.

Uses all pending V units, without filtering by proposed class. Keep the entire
old target and add one adjacent sentence (ASR) or up to three cues per side
(unpunctuated captions), subject to the actual local tokenizer's 384 limit.
Overlaps are explicit: candidates cannot be added to evaluation as extra rows.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs/beto-v3'
META = ROOT / 'artifacts/beto-v3/recovery-01'
OUT = BASE / 'recovery-01'
PARENT = BASE / 'phase-b-gap-02/selected-444/all-development-units.json'
GUIDE = ROOT / 'docs/beto-v3/guia-etiquetado-v3.md'
LEDGER = ROOT / 'artifacts/beto-v3/budget-ledger-current.json'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def immutable(p, obj, check):
    if p.exists():
        assert read(p) == obj, f'Frozen artifact differs: {p}'
    else:
        assert not check, f'Missing artifact: {p}'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def source_path(sid):
    paths = [BASE / f'phase-b-gap-02/{sid}/cues.json',
             BASE / f'phase-b-completion-01/new-sources/{sid}/asr/cues.json',
             BASE / f'acquisition/{sid}/cues.json']
    return next(p for p in paths if p.exists())


def bounds(u, spans):
    if u.get('source_char_span'):
        return tuple(u['source_char_span'])
    indices = u['cue_indices']
    assert indices == list(range(min(indices), max(indices) + 1))
    return spans[min(indices)][0], spans[max(indices)][1]


def main(check=False):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(
        ROOT / 'apps/ml/storage/models/beto-v1-gold-source-aware', local_files_only=True)
    def count(text):
        return len(tok(text, truncation=False)['input_ids'])
    rows = read(PARENT)['items']
    # Preparation is immutable even after real responses consume its new hashes.
    baseline = META / 'before/budget-ledger-current.json'
    ledger = read(baseline if baseline.exists() else LEDGER)
    frozen_hashes = {r['input_sha256'] for r in rows}
    candidates, deferred, sources = [], [], []
    pending = [r for r in rows if r['partition'] == 'V' and not r.get('accepted_label')]
    for sid in sorted({u['source_id'] for u in pending}):
        p = source_path(sid)
        cues = read(p)
        full = ' '.join(c['text'].strip() for c in cues)
        spans, pos = [], 0
        for c in cues:
            end = pos + len(c['text'].strip())
            spans.append((pos, end))
            pos = end + 1
        sources.append({'path': str(p.relative_to(ROOT)), 'sha256': sha(p)})
        sentences = sorted({0, len(full)} | {m.end() for m in re.finditer(r'[.!?](?:[”"»])?(?:\s+|$)', full)})
        for u in sorted((u for u in pending if u['source_id'] == sid), key=lambda u: u['segment_id']):
            a, z = bounds(u, spans)
            assert norm(full[a:z]) == u['text'], u['segment_id']
            if len(norm(re.sub(r'\[[^\]]*\]', '', u['text'])).split()) < 5:
                deferred.append({'segment_id': u['segment_id'], 'reason': 'Insufficient lexical content; requires audio review, not added caption context.'})
                continue
            if 'asr' in p.parts:
                left = [max((b for b in sentences if b < a), default=a)]
                right = [min((b for b in sentences if b > z), default=z)]
            else:
                left = sorted([x for x, y in spans if x < a], reverse=True)[:3]
                right = [y for x, y in spans if y > z][:3]
            options = []
            for x in [a] + left:
                for y in [z] + right:
                    text = norm(full[x:y])
                    n = count(text)
                    if text != u['text'] and n <= 384:
                        # Prefer two-sided evidence, then more authentic context.
                        options.append(((int(x < a) + int(y > z), y-x), x, y, text, n))
            if not options:
                deferred.append({'segment_id': u['segment_id'], 'reason': 'No adjacent complete sentence/cue fits without dropping original text or exceeding 384 tokens.'})
                continue
            _, x, y, text, n = max(options)
            h = hashlib.sha256(text.encode()).hexdigest()
            assert h not in frozen_hashes
            frozen_hashes.add(h)
            pieces = [{'cue_index': i, 'cue_char_start': max(x, b)-b, 'cue_char_end': min(y, e)-b}
                      for i, (b, e) in enumerate(spans) if b < y and e > x]
            reconstructed = ' '.join(cues[q['cue_index']]['text'].strip()[q['cue_char_start']:q['cue_char_end']] for q in pieces)
            assert norm(reconstructed) == text
            overlaps = []
            for old in rows:
                if old['source_id'] != sid:
                    continue
                b, e = bounds(old, spans)
                if b < y and e > x:
                    overlaps.append(old['segment_id'])
            candidates.append({'segment_id': u['segment_id'] + '-recovery01',
                'parent_segment_id': u['segment_id'], 'parent_input_sha256': u['input_sha256'],
                'source_id': sid, 'partition': 'V', 'family_id': u['family_id'],
                'text': text, 'input_sha256': h, 'guide_sha256': sha(GUIDE),
                'source_path': str(p.relative_to(ROOT)), 'source_sha256': sha(p),
                'source_char_span': [x, y], 'parent_source_char_span': [a, z],
                'cue_pieces': pieces, 'tokens_with_specials': n, 'would_truncate_tokens': 0,
                'overlapping_existing_ids': sorted(overlaps),
                'status': 'candidate_requires_discourse_and_two_pass_review',
                'accepted_label': None, 'training_eligible': False,
                'context': None, 'automatic_reference_replacement': False})
    assert len(candidates) <= ledger['annotation_budget_remaining'] - 200
    immutable(OUT / 'candidates.json', {'items': candidates}, check)
    packets = []
    for start in range(0, len(candidates), 10):
        path = OUT / 'inputs' / f'batch-{start//10+1:03}.json'
        packet = {'guide': GUIDE.read_text(encoding='utf-8'),
                  'items': [{k: r[k] for k in ['segment_id', 'text', 'input_sha256', 'guide_sha256']}
                            for r in candidates[start:start+10]]}
        immutable(path, packet, check)
        packets.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})
    report = {'version': 'recovery-01', 'pending_V_examined': len(pending),
        'prepared_candidates': len(candidates), 'deferred': deferred,
        'selection': 'All pending V, no class/proposal/prediction filter. Original targets retained in full; only contiguous source text added.',
        'parent_dataset': str(PARENT.relative_to(ROOT)), 'parent_sha256': sha(PARENT),
        'guide_sha256': sha(GUIDE), 'source_manifest': sources, 'packets': packets,
        'candidates_sha256': sha(OUT / 'candidates.json'),
        'annotation_unique_at_preparation': ledger['new_unique_annotation_proposals'],
        'new_annotation_inputs_consumed': 0, 'projected_unique_if_all_annotated': ledger['new_unique_annotation_proposals'] + len(candidates),
        'remaining_if_all_annotated': ledger['annotation_budget_remaining'] - len(candidates),
        'S_planning_allowance': 200, 'S_content_opened': False,
        'accepted_reference_gains': 0, 'C_ready': False,
        'first_pass_completed': 0, 'blind_review_completed': 0,
        'integration_requirements': [
            'Count new hashes when real first-pass responses are saved; keep prior consumption.',
            'Require review in a context without prior responses; never simulate an isolated review.',
            'Adjudicate discourse, scope and literal evidence; context recovery does not guarantee a unique label.',
            'Resolve all overlapping candidate/old intervals before evaluation: no additive quota gains from duplicate text.',
            'Use a new versioned integration and update accounting checks before any proposals; selected-444 accounting currently fixes total at 938.',
            'Source admission and H/T/V/S freezing remain required before C.']}
    immutable(META / 'preparation.json', report, check)
    print(json.dumps({k: report[k] for k in ['pending_V_examined', 'prepared_candidates', 'new_annotation_inputs_consumed', 'remaining_if_all_annotated', 'C_ready']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-only', action='store_true')
    main(parser.parse_args().check_only)
