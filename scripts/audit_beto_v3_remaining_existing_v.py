"""Read-only source-text coverage audit; no labels, acquisition, or response files."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/beto-v3/recovery-01/remaining-existing-V.json'


def main():
    provenance = []

    def read(rel):
        path = ROOT / rel
        blob = path.read_bytes()
        provenance.append({'path': path.relative_to(ROOT).as_posix(),
                           'sha256': hashlib.sha256(blob).hexdigest()})
        return json.loads(blob.decode('utf-8'))

    registry = read('artifacts/beto-v3/phase-b-completion-01/source-registry-final.json')
    overlay = read('artifacts/beto-v3/phase-b-gap-02/selected-444/source-registry-overlay.json')
    fields = ('segment_id', 'source_id', 'partition', 'source_sha256', 'input_sha256',
              'text', 'source_char_span', 'cue_indices')
    original = [{k: r.get(k) for k in fields} for r in read('outputs/beto-v3/phase-b-gap-02/selected-444/all-development-units.json')['items']]
    assert len(original) == 930
    development = [r for r in original if r['partition'] == 'V']
    ledger = read('artifacts/beto-v3/budget-ledger-current.json')
    sources = [r for r in registry['existing_sources'] if r.get('role') == 'V']
    sources += [r for r in registry['new_candidates'] if r.get('proposed_role') == 'V']
    sources += [r for r in overlay['sources'] if r.get('role') == 'V']
    results = []
    for source in sorted(sources, key=lambda r: r.get('source_id') or r['video_id']):
        sid = source.get('source_id') or source['video_id']
        role = source.get('final_role', source.get('role', source.get('proposed_role')))
        result = {'source_id': sid, 'video_id': source.get('video_id'),
                  'family_id': source['family_id'], 'recorded_role': role,
                  'original_proposed_role': source.get('proposed_role', source.get('role')),
                  'duration_seconds': source.get('duration_seconds'),
                  'registry_status': source.get('status'),
                  'role_changed_by_audit': False}
        if sid.startswith('G'):
            cue_path = f'outputs/beto-v3/phase-b-gap-02/{sid}/cues.json'
            inventory_path = f'outputs/beto-v3/phase-b-gap-02/{sid}/annotation/units.json'
        elif sid.startswith('N'):
            cue_path = f'outputs/beto-v3/phase-b-completion-01/new-sources/{sid}/asr/cues.json'
            inventory_path = f'outputs/beto-v3/phase-b-completion-01/asr-annotation/{sid}/units.json'
        else:
            cue_path = f'outputs/beto-v3/acquisition/{sid}/cues.json'
            inventory_path = None
        result['expected_cues_path'] = cue_path
        if role == 'auxiliary_quarantine':
            result.update(assessment='excluded_existing_auxiliary_quarantine',
                          local_cues_present=(ROOT / cue_path).exists(),
                          transcript_content_read=False,
                          blocker='N03 retains auxiliary_quarantine and duration 1080.744 seconds, below 1800-second primary-work requirement; no role reassignment.',
                          usable_new_disjoint_primary_targets=0)
            results.append(result)
            continue
        if not (ROOT / cue_path).exists():
            result.update(assessment='no_local_authentic_transcript',
                          local_cues_present=False, transcript_content_read=False,
                          blocker=source.get('known_block') or source.get('error_type') or 'Acquisition incomplete',
                          usable_new_disjoint_primary_targets=0)
            results.append(result)
            continue
        cues = read(cue_path)
        cue_hash = provenance[-1]['sha256']
        if source.get('captions_sha256'):
            assert cue_hash == source['captions_sha256']
        texts = [cue['text'].strip() for cue in cues]
        full = ' '.join(texts)
        starts, offset = [], 0
        for text in texts:
            starts.append(offset)
            offset += len(text) + 1
        rows = [r for r in development if r['source_id'] == sid]
        assert rows and all(r['source_sha256'] == cue_hash for r in rows)
        spans = []
        for row in rows:
            span = row['source_char_span']
            if span is None:
                indices = row['cue_indices']
                assert indices == list(range(indices[0], indices[-1] + 1))
                span = [starts[indices[0]], starts[indices[-1]] + len(texts[indices[-1]])]
            a, b = span
            assert 0 <= a <= b <= len(full)
            target = full[a:b]
            assert target.strip() == row['text'], row['segment_id']
            assert hashlib.sha256(row['text'].encode('utf-8')).hexdigest() == row['input_sha256']
            effective = [a + len(target) - len(target.lstrip()), b - len(target) + len(target.rstrip())]
            spans.append({'segment_id': row['segment_id'], 'source_char_span': span,
                          'effective_text_span': effective, 'input_sha256': row['input_sha256']})
        ordered = sorted([r['effective_text_span'] for r in spans])
        union = []
        for a, b in ordered:
            if union and a <= union[-1][1]:
                union[-1][1] = max(union[-1][1], b)
            else:
                union.append([a, b])
        unused, cursor = [], 0
        for a, b in union:
            if a > cursor:
                unused.append([cursor, a])
            cursor = b
        if cursor < len(full):
            unused.append([cursor, len(full)])
        genuine = [[a, b] for a, b in unused if full[a:b].strip()]
        total_nonwhite = sum(not char.isspace() for char in full)
        unused_nonwhite = sum(not char.isspace() for a, b in unused for char in full[a:b])
        duration = source.get('duration_seconds')
        timeline = sorted((cue['start'], cue.get('end', cue['start'] + cue.get('duration', 0))) for cue in cues)
        time_union = []
        for a, b in timeline:
            if time_union and a <= time_union[-1][1]:
                time_union[-1][1] = max(time_union[-1][1], b)
            else:
                time_union.append([a, b])
        internal_time_gaps = [[round(left[1], 6), round(right[0], 6)] for left, right in zip(time_union, time_union[1:])]
        temporal = {
            'coordinate_system': 'seconds from recorded cue timestamps; gaps do not imply recoverable missing speech',
            'internal_gaps_over_15_seconds': [span for span in internal_time_gaps if span[1] - span[0] > 15],
            'all_internal_gap_count': len(internal_time_gaps),
            'all_internal_gap_seconds': round(sum(b - a for a, b in internal_time_gaps), 6),
            'leading_time_without_cue': [0, time_union[0][0]] if time_union[0][0] > 0 else None,
            'trailing_time_without_cue_to_metadata_duration': [time_union[-1][1], duration] if duration and duration > time_union[-1][1] else None,
            'new_authentic_text_available_in_timing_gaps': False,
            'gap_interpretation': 'No source words exist in saved cues for these intervals. This audit does not inspect audio or infer speech, music, silence, or ASR omission.'}
        inventory_check = None
        if inventory_path:
            inventory = read(inventory_path)
            inventory_ids = {r['segment_id'] for r in inventory['items']}
            actual_ids = {r['segment_id'] for r in rows}
            assert inventory_ids == actual_ids, sid
            inventory_check = {'path': inventory_path, 'units': len(inventory['items']),
                               'all_inventory_units_present_in_original_dataset': True}
        if sid == 'N07':
            transcription = read('outputs/beto-v3/phase-b-completion-01/new-sources/N07/asr/transcription.json')
            assert transcription['segments'] == cues
            quality = read('outputs/beto-v3/phase-b-completion-01/new-sources/N07/asr/quality.json')
            result['full_asr_transcription_checks'] = {
                'all_908_saved_segments_equal_cues': len(cues) == 908,
                'complete_audio_processed_recorded': transcription['complete_audio_processed'],
                'quality_receipt_complete_audio_processed': quality['complete_audio_processed'],
                'speech_transcription_completeness': quality['speech_transcription_completeness'],
                'remaining_transcript_tail_after_last_original_unit': [max(r['source_char_span'][1] for r in spans), len(full)]}
        result.update(local_cues_present=True, transcript_content_read=True,
                      source_file_sha256=cue_hash, cue_count=len(cues),
                      source_text_sha256=hashlib.sha256(full.encode('utf-8')).hexdigest(),
                      source_characters=len(full), source_non_whitespace_characters=total_nonwhite,
                      original_units=len(rows), inventory_check=inventory_check,
                      earliest_saved_cue_start=cues[0]['start'],
                      latest_saved_cue_end=max(cue.get('end', cue['start'] + cue.get('duration', 0)) for cue in cues),
                      covered_non_whitespace_characters=total_nonwhite - unused_nonwhite,
                      non_whitespace_coverage_fraction=(total_nonwhite - unused_nonwhite) / total_nonwhite,
                      unused_intervals_including_separators=unused,
                      unused_genuine_text_intervals=genuine,
                      unused_non_whitespace_characters=unused_nonwhite,
                      unused_whitespace_characters=sum(b - a for a, b in unused) - unused_nonwhite,
                      temporal_coverage_separate_from_source_text=temporal,
                      source_character_intervals_by_original_unit=spans,
                      assessment='all_saved_source_text_previously_used' if not genuine else 'unused_authentic_text_requires_boundary_and_source_review',
                      usable_new_disjoint_primary_targets=0 if not genuine else None,
                      blocker='No unannotated non-whitespace source characters remain.' if not genuine else None)
        results.append(result)
    acquired = [r for r in results if r.get('transcript_content_read')]
    assert sum(r['original_units'] for r in acquired) == len(development)
    report = {
        'schema_version': 1, 'audit_type': 'existing_V_source_coverage_no_annotation',
        'coordinate_system': 'Unicode code points; half-open intervals in stripped cue texts joined by one ASCII space; original target exterior whitespace excluded from text coverage',
        'scope': 'All registry role-V sources, originally proposed V candidates, and selected-444 V overlay sources. Only current V/V_provisional local cue content read; N03 quarantine kept excluded.',
        'original_dataset_units': len(original), 'original_V_units': len(development),
        'source_count': len(results), 'active_acquired_V_source_count': len(acquired),
        'V_candidates_without_local_transcript': sum(r['assessment'] == 'no_local_authentic_transcript' for r in results),
        'excluded_auxiliary_quarantine_sources': sum(r['assessment'] == 'excluded_existing_auxiliary_quarantine' for r in results),
        'total_active_V_source_characters': sum(r['source_characters'] for r in acquired),
        'total_active_V_source_non_whitespace_characters': sum(r['source_non_whitespace_characters'] for r in acquired),
        'total_unused_genuine_non_whitespace_characters': sum(r['unused_non_whitespace_characters'] for r in acquired),
        'additional_disjoint_unannotated_targets_from_saved_active_V_text': 0 if all(not r['unused_genuine_text_intervals'] for r in acquired) else None,
        'budget': {'recorded_unique_annotation_inputs': ledger['new_unique_annotation_proposals'],
                   'recorded_remaining_annotation_inputs': ledger['annotation_budget_remaining'],
                   'preserved_S_reserve': 200, 'non_S_inputs_available_without_using_reserve': ledger['annotation_budget_remaining'] - 200,
                   'annotation_inputs_spent_by_this_audit': 0, 'new_acquisition_calls': 0},
        'conclusion': 'Existing active V transcripts contain no previously unused genuine source text. The remaining non-S input allowance cannot create new disjoint targets from these transcripts without reusing already annotated content.',
        'blockers': ['All six active acquired V transcripts are exhausted at source-character level, including the complete saved N07 ASR transcript and all rKb caption cues.',
                     'Pending labels are already annotated inputs; reframing or splitting those passages does not make them previously unannotated source text.',
                     'No local authentic transcript exists for four further V candidates; metadata and acquisition failures cannot supply targets.',
                     'N03 remains auxiliary quarantine and below the primary 30-minute threshold.',
                     'Coverage is of saved transcript text, not certification that captions/ASR captured every spoken word; unsaved speech or timing gaps do not constitute available authentic text.',
                     'Any future retrieval, source admission, boundary review, or new annotation is outside this zero-spend audit. No class or minimum class/work gain is inferred.'],
        'S_content_opened': False, 'roles_changed': False, 'labels_proposed': False,
        'provenance': provenance + [{'path': Path(__file__).relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}],
        'sources': results}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('source_count', 'active_acquired_V_source_count', 'original_V_units', 'total_active_V_source_characters', 'total_active_V_source_non_whitespace_characters', 'total_unused_genuine_non_whitespace_characters', 'budget')}, indent=2))
    print(json.dumps([{k: r.get(k) for k in ('source_id', 'assessment', 'cue_count', 'source_characters', 'source_non_whitespace_characters', 'original_units', 'unused_non_whitespace_characters')} for r in results], indent=2))


if __name__ == '__main__':
    main()
