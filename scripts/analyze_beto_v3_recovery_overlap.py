"""Deterministic geometry-only audit. Never changes references or reads review files."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / 'outputs/beto-v3/recovery-01/candidates.json'
EXISTING = ROOT / 'outputs/beto-v3/phase-b-gap-02/selected-444/all-development-units.json'
OUTPUT = ROOT / 'artifacts/beto-v3/recovery-01/overlap-audit.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def intersection(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return [lo, hi] if lo < hi else None


def subtract(span, blocks):
    pieces = [span]
    for block in sorted(blocks):
        updated = []
        for a, b in pieces:
            overlap = intersection([a, b], block)
            if overlap is None:
                updated.append([a, b])
            else:
                if a < overlap[0]:
                    updated.append([a, overlap[0]])
                if overlap[1] < b:
                    updated.append([overlap[1], b])
        pieces = updated
    return pieces


def main():
    candidates = json.loads(CANDIDATES.read_text(encoding='utf-8'))['items']
    # Strict projection: review responses, proposals, evidence and class values
    # are never used by this computation or copied to its output.
    fields = ('segment_id', 'source_id', 'family_id', 'partition', 'text',
              'input_sha256', 'source_sha256', 'source_char_span', 'cue_indices',
              'status', 'reference_status')
    existing = []
    for raw in json.loads(EXISTING.read_text(encoding='utf-8'))['items']:
        row = {k: raw.get(k) for k in fields}
        row['has_accepted_reference'] = raw.get('accepted_label') is not None
        existing.append(row)
    sources = {}
    for candidate in candidates:
        key = candidate['source_sha256']
        if key in sources:
            continue
        path = ROOT / candidate['source_path'].replace('\\', '/')
        assert digest(path) == key, path
        cues = json.loads(path.read_text(encoding='utf-8'))
        texts = [cue['text'].strip() for cue in cues]
        starts, offset = [], 0
        for text in texts:
            starts.append(offset)
            offset += len(text) + 1
        sources[key] = {'path': path.relative_to(ROOT).as_posix(),
                        'text': ' '.join(texts), 'starts': starts, 'cues': texts}

    def locate(row):
        source = sources[row['source_sha256']]
        span = row.get('source_char_span')
        basis = 'declared_source_char_span'
        if span is None:
            indices = row['cue_indices']
            assert indices == list(range(indices[0], indices[-1] + 1))
            span = [source['starts'][indices[0]],
                    source['starts'][indices[-1]] + len(source['cues'][indices[-1]])]
            basis = 'derived_from_contiguous_cue_indices'
        a, b = span
        fragment = source['text'][a:b]
        assert fragment.strip() == row['text'], row['segment_id']
        assert hashlib.sha256(row['text'].encode('utf-8')).hexdigest() == row['input_sha256'], row['segment_id']
        effective = [a + len(fragment) - len(fragment.lstrip()), b - len(fragment) + len(fragment.rstrip())]
        return {'source_char_span': span, 'effective_text_span': effective, 'span_basis': basis}

    relevant = [r for r in existing if r['source_sha256'] in sources]
    located = {r['segment_id']: locate(r) for r in relevant}
    candidate_locations = {r['segment_id']: locate(r) for r in candidates}
    lookup = {r['segment_id']: r for r in existing}
    results = []
    for c in sorted(candidates, key=lambda r: r['segment_id']):
        loc = candidate_locations[c['segment_id']]
        overlaps = []
        for row in relevant:
            if row['source_sha256'] != c['source_sha256']:
                continue
            rloc = located[row['segment_id']]
            span = intersection(loc['source_char_span'], rloc['source_char_span'])
            if span is None:
                continue
            text_span = intersection(loc['effective_text_span'], rloc['effective_text_span'])
            overlaps.append({k: row[k] for k in ('segment_id', 'source_id', 'family_id', 'partition', 'input_sha256', 'status', 'reference_status', 'has_accepted_reference')} | rloc | {
                'is_parent': row['segment_id'] == c['parent_segment_id'],
                'overlap_span': span, 'overlap_characters': span[1] - span[0],
                'effective_text_overlap_span': text_span,
                'effective_text_overlap_characters': text_span[1] - text_span[0] if text_span else 0})
        overlaps.sort(key=lambda r: r['segment_id'])
        accepted = [r for r in overlaps if r['has_accepted_reference'] and r['effective_text_overlap_characters']]
        pending = [r for r in overlaps if not r['has_accepted_reference']]
        parent = lookup[c['parent_segment_id']]
        assert parent['input_sha256'] == c['parent_input_sha256']
        assert located[parent['segment_id']]['source_char_span'] == c['parent_source_char_span']
        assert set(c['overlapping_existing_ids']) == {r['segment_id'] for r in overlaps}
        peers = []
        for other in candidates:
            if other['segment_id'] == c['segment_id'] or other['source_sha256'] != c['source_sha256']:
                continue
            span = intersection(loc['effective_text_span'], candidate_locations[other['segment_id']]['effective_text_span'])
            if span:
                peers.append({'segment_id': other['segment_id'], 'effective_text_overlap_span': span, 'characters': span[1] - span[0]})
        uncovered = subtract(loc['effective_text_span'], [r['effective_text_span'] for r in overlaps])
        uncovered_non_whitespace = sum(not char.isspace() for a, b in uncovered for char in sources[c['source_sha256']]['text'][a:b])
        results.append({k: c[k] for k in ('segment_id', 'parent_segment_id', 'source_id', 'source_sha256', 'input_sha256', 'partition')} | loc | {
            'parent_has_accepted_reference': parent['has_accepted_reference'],
            'existing_overlaps': overlaps,
            'candidate_overlaps': sorted(peers, key=lambda r: r['segment_id']),
            'accepted_overlap_ids': [r['segment_id'] for r in accepted],
            'pending_overlap_ids': [r['segment_id'] for r in pending],
            'remaining_intervals_after_preserving_accepted': subtract(loc['effective_text_span'], [r['effective_text_span'] for r in accepted]),
            'uncovered_intervals_relative_to_all_existing_rows': uncovered,
            'uncovered_non_whitespace_characters_relative_to_all_existing_rows': uncovered_non_whitespace,
            'geometrically_eligible_after_pending_supersession': not accepted,
            'integration_decision': 'blocked_by_accepted_reference_overlap' if accepted else 'eligible_geometry_only_requires_annotation_and_peer_conflict_resolution'})
    summary = {
        'existing_rows': len(existing), 'existing_accepted_rows': sum(r['has_accepted_reference'] for r in existing),
        'existing_pending_rows': sum(not r['has_accepted_reference'] for r in existing),
        'candidate_count': len(results), 'source_count': len(sources), 'source_rows_geometry_verified': len(relevant),
        'parents_accepted': sum(r['parent_has_accepted_reference'] for r in results),
        'candidates_blocked_by_accepted_overlap': sum(bool(r['accepted_overlap_ids']) for r in results),
        'candidates_eligible_geometry_only': sum(r['geometrically_eligible_after_pending_supersession'] for r in results),
        'candidate_existing_overlap_pairs': sum(len(r['existing_overlaps']) for r in results),
        'candidate_accepted_overlap_pairs': sum(len(r['accepted_overlap_ids']) for r in results),
        'candidate_pending_overlap_pairs': sum(len(r['pending_overlap_ids']) for r in results),
        'unique_accepted_overlapping_rows': len({i for r in results for i in r['accepted_overlap_ids']}),
        'unique_pending_overlapping_rows': len({i for r in results for i in r['pending_overlap_ids']}),
        'candidate_peer_overlap_pairs': sum(len(r['candidate_overlaps']) for r in results) // 2,
        'candidates_with_novel_non_whitespace_source_text': sum(bool(r['uncovered_non_whitespace_characters_relative_to_all_existing_rows']) for r in results),
        'candidates_with_declared_span_trailing_or_leading_whitespace': sum(r['source_char_span'] != r['effective_text_span'] for r in results),
        'integration_decision_counts': dict(Counter(r['integration_decision'] for r in results)),
    }
    report = {'schema_version': 1, 'audit_type': 'geometry_only_no_label_acceptance',
              'coordinate_system': 'Unicode code points, half-open intervals, one ASCII space between stripped authentic cue texts; effective spans remove target exterior whitespace',
              'reference_rule': 'accepted_label non-null identifies preserved accepted reference; reference_status retained for audit; generic status is stale for some accepted rows',
              'provenance': {'candidates': {'path': CANDIDATES.relative_to(ROOT).as_posix(), 'sha256': digest(CANDIDATES)},
                             'existing': {'path': EXISTING.relative_to(ROOT).as_posix(), 'sha256': digest(EXISTING)},
                             'script': {'path': Path(__file__).relative_to(ROOT).as_posix(), 'sha256': digest(Path(__file__))},
                             'sources': [{'path': v['path'], 'sha256': k} for k, v in sorted(sources.items())]},
              'summary': summary,
              'policy': ['Preserve every prior accepted reference and its original text/hash unchanged.',
                         'Do not append a full candidate whose effective target overlaps any accepted reference.',
                         'Pending rows may be explicitly superseded only after candidate annotation and adjudication; retain immutable originals and supersession lineage.',
                         'Candidates overlapping each other cannot both enter evaluation; resolve interval conflicts explicitly before integration.',
                         'Residual intervals are geometric opportunities only, not annotated targets: clipping requires new target hashes and new reviews; never transfer a whole-candidate label to a clipped interval.',
                         'A parent pending status never overrides an accepted neighbor. Preserve partition and source identity; source hashes define the authentic coordinate domain.'],
              'checks': {'all_candidate_and_relevant_existing_texts_reconstructed': True,
                         'all_input_hashes_verified': True, 'all_source_file_hashes_verified': True,
                         'all_parent_hashes_and_spans_verified': True, 'declared_overlap_lists_match_recomputation': True},
              'items': results}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
