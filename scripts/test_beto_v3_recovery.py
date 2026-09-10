"""Synthetic recovery policy/accounting tests; never open annotation responses."""
import copy
import unittest
from unittest.mock import patch

import beto_v3_recovery_accounting as accounting
from integrate_beto_v3_recovery import choose_effective


def old(sid, label=None):
    return {'segment_id': sid, 'accepted_label': label}


def candidate(sid, parent, span, overlaps, source='source-1'):
    return {'segment_id': sid, 'parent_segment_id': parent,
            'source_id': source, 'source_char_span': span,
            'overlapping_existing_ids': overlaps}


class EffectivePolicyTests(unittest.TestCase):
    def test_resolved_disjoint_target_replaces_pending_parent(self):
        u = candidate('new', 'pending', [10, 20], ['pending'])
        selected, disposition = choose_effective([old('pending'), old('accepted', 'class-a')],
                                                 {'new': u}, {'new': {'resolved_label': 'class-b'}})
        self.assertEqual(selected, [u])
        self.assertEqual(disposition['new']['status'], 'accepted_replacement_of_pending_parent')

    def test_accepted_neighbor_wins_even_with_same_label(self):
        u = candidate('new', 'pending', [10, 20], ['pending', 'neighbor'])
        selected, disposition = choose_effective([old('pending'), old('neighbor', 'class-a')],
                                                 {'new': u}, {'new': {'resolved_label': 'class-a'}})
        self.assertEqual(selected, [])
        self.assertEqual(disposition['new']['conflicts'], ['neighbor'])

    def test_overlapping_peers_do_not_both_enter_evaluation(self):
        units = {'b': candidate('b', 'p2', [19, 30], ['p2']),
                 'a': candidate('a', 'p1', [10, 20], ['p1'])}
        decisions = {sid: {'resolved_label': 'class-a'} for sid in units}
        before = copy.deepcopy((units, decisions))
        selected, disposition = choose_effective([old('p1'), old('p2')], units, decisions)
        self.assertEqual([r['segment_id'] for r in selected], ['a'])
        self.assertEqual(disposition['b']['conflicts'], ['a'])
        self.assertEqual((units, decisions), before)
        self.assertEqual(choose_effective([old('p1'), old('p2')], dict(reversed(list(units.items()))), decisions),
                         (selected, disposition))

    def test_touching_half_open_intervals_are_disjoint(self):
        units = {'a': candidate('a', 'p1', [10, 20], ['p1']),
                 'b': candidate('b', 'p2', [20, 30], ['p2'])}
        selected, _ = choose_effective([old('p1'), old('p2')], units,
                                       {sid: {'resolved_label': 'class-a'} for sid in units})
        self.assertEqual(len(selected), 2)

    def test_same_coordinates_in_distinct_sources_do_not_conflict(self):
        units = {'a': candidate('a', 'p1', [10, 20], ['p1']),
                 'b': candidate('b', 'p2', [10, 20], ['p2'], source='source-2')}
        selected, _ = choose_effective([old('p1'), old('p2')], units,
                                       {sid: {'resolved_label': 'class-a'} for sid in units})
        self.assertEqual(len(selected), 2)

    def test_unresolved_and_unadjudicated_candidates_add_no_references(self):
        units = {'a': candidate('a', 'p1', [10, 20], ['p1']),
                 'b': candidate('b', 'p2', [20, 30], ['p2'])}
        selected, disposition = choose_effective([old('p1'), old('p2')], units,
                                                 {'a': {'resolved_label': None}})
        self.assertEqual(selected, [])
        self.assertTrue(all(d['status'] == 'pending_reference' for d in disposition.values()))

    def test_accepted_parent_cannot_be_replaced(self):
        with self.assertRaises(AssertionError):
            choose_effective([old('p1', 'class-a')],
                             {'a': candidate('a', 'p1', [10, 20], ['p1'])},
                             {'a': {'resolved_label': 'class-a'}})


class AccountingTests(unittest.TestCase):
    BASE = {'new_unique_annotation_proposals': 938,
            'phase_B_second_review_units': 700, 'phase_B_second_review_batches': 25,
            'phase_B_second_review_calls': 8}

    def compute(self, first, second, manifests):
        def fake_read(path):
            if path == accounting.META / 'before/budget-ledger-current.json':
                return copy.deepcopy(self.BASE)
            if path == accounting.META / 'preparation.json':
                return {'parent_dataset': 'synthetic-parent.json'}
            if path == accounting.ROOT / 'synthetic-parent.json':
                return {'items': [{'input_sha256': 'historical'}]}
            raise AssertionError(f'Unexpected file access: {path}')
        with patch.object(accounting, 'responses', return_value=({}, {'first-pass': first, 'second-review': second}, manifests)), \
                patch.object(accounting, 'read', side_effect=fake_read):
            return accounting.expected_ledger()[0]

    def test_two_passes_same_input_count_once_and_repeat_is_idempotent(self):
        first = {'a': {'input_sha256': 'hash-a'}}
        second = {'a': {'input_sha256': 'hash-a'}}
        manifest = [{'stage': 'first-pass', 'session': 'first'},
                    {'stage': 'second-review', 'session': 'second'}]
        ledger = self.compute(first, second, manifest)
        self.assertEqual(ledger['new_unique_annotation_proposals'], 939)
        self.assertEqual(ledger['annotation_budget_remaining'], 261)
        self.assertEqual(ledger['phase_B_second_review_units'], 701)
        self.assertEqual(ledger['phase_B_second_review_calls'], 9)
        self.assertEqual(ledger, self.compute(first, second, manifest))

    def test_partial_batches_count_actual_hash_union_and_one_session(self):
        first = {'a': {'input_sha256': 'hash-a'}, 'b': {'input_sha256': 'hash-b'}}
        second = {'a': {'input_sha256': 'hash-a'}, 'c': {'input_sha256': 'hash-c'}}
        manifest = [{'stage': 'second-review', 'session': 'second'},
                    {'stage': 'second-review', 'session': 'second'}]
        ledger = self.compute(first, second, manifest)
        self.assertEqual(ledger['new_unique_annotation_proposals'], 941)
        self.assertEqual(ledger['phase_B_second_review_batches'], 27)
        self.assertEqual(ledger['phase_B_second_review_calls'], 9)

    def test_historical_hash_cannot_be_charged_as_new(self):
        with self.assertRaises(AssertionError):
            self.compute({'a': {'input_sha256': 'historical'}}, {}, [])

    def test_reserve_of_200_is_enforced(self):
        with self.assertRaises(AssertionError):
            self.compute({str(i): {'input_sha256': f'new-{i}'} for i in range(63)}, {}, [])

    def test_removed_second_review_event_rejected_with_unchanged_unique_count(self):
        expected = self.compute({'a': {'input_sha256': 'hash-a'}}, {}, [])
        actual = copy.deepcopy(expected)
        # Its input still occurs in the first pass, so removing the second pass
        # does not change the cumulative unique-input count.
        self.assertEqual(actual['new_unique_annotation_proposals'], 939)
        saved_event = accounting.META / 'response-events/second-review/batch-001.json'
        for check_only in (False, True):
            with self.subTest(check_only=check_only), \
                    patch.object(accounting, 'expected_ledger', return_value=(expected, {}, {}, [])), \
                    patch.object(accounting, 'read', return_value=actual) as read_mock, \
                    patch.object(accounting.Path, 'glob', return_value=iter([saved_event])), \
                    patch.object(accounting, 'save') as save_mock, \
                    patch.object(accounting, 'immutable') as immutable_mock:
                with self.assertRaisesRegex(AssertionError, 'Previously accounted response removed'):
                    accounting.account(check_only=check_only)
                read_mock.assert_called_once_with(accounting.LEDGER)
                save_mock.assert_not_called()
                immutable_mock.assert_not_called()

    def test_second_review_counters_cannot_regress_with_unchanged_unique_count(self):
        expected = self.compute({'a': {'input_sha256': 'hash-a'}}, {}, [])
        for key in ('phase_B_second_review_units', 'phase_B_second_review_batches',
                    'phase_B_second_review_calls', 'recovery01_second_review_units'):
            actual = copy.deepcopy(expected)
            actual[key] += 1
            self.assertEqual(actual['new_unique_annotation_proposals'], expected['new_unique_annotation_proposals'])
            with self.subTest(counter=key), \
                    patch.object(accounting, 'expected_ledger', return_value=(expected, {}, {}, [])), \
                    patch.object(accounting, 'read', return_value=actual) as read_mock, \
                    patch.object(accounting.Path, 'glob', return_value=iter([])), \
                    patch.object(accounting, 'save') as save_mock, \
                    patch.object(accounting, 'immutable') as immutable_mock:
                with self.assertRaisesRegex(AssertionError, f'Counter cannot regress: {key}'):
                    accounting.account()
                read_mock.assert_called_once_with(accounting.LEDGER)
                save_mock.assert_not_called()
                immutable_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
