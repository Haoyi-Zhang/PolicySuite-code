"""Portable own finite oracles connected to actual production routines.

No historical source copy, campaign, network, deletion or measured clock.
"""
from __future__ import annotations
import copy
import itertools
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import checker
import optimize
import semantics


def reference(q, supports):
    """Subset-enumerated optima, then independent complete-child closure.

    Reconstruct the specified pivot/tie order, not the production DP algorithm.
    Each optimum is computed by request subset enumeration, without recurrence.
    """
    incidence = [frozenset(i for i, support in enumerate(supports) if support & (1 << x))
                 for x in range(q)]
    representatives = {}
    for x, row in enumerate(incidence):
        if row:
            representatives.setdefault(row, x)
    universe = frozenset(i for i, support in enumerate(supports) if support)

    def minimum(obligations):
        for size in range(q + 1):
            for chosen in itertools.combinations(range(q), size):
                covered = frozenset().union(*(incidence[x] for x in chosen))
                if obligations <= covered:
                    return size
        raise ValueError('uncoverable finite family')

    pending = [universe]; states = {}
    while pending:
        obligations = pending.pop()
        mask = sum(1 << i for i in obligations)
        if mask in states:
            continue
        pivot = min(obligations, key=lambda i: (sum(i in row for row in representatives), i)) if obligations else -1
        states[mask] = (minimum(obligations), pivot)
        if obligations:
            pending.extend(obligations - row for row in representatives if pivot in row)
    remaining = universe; suite = []
    while remaining:
        mask = sum(1 << i for i in remaining)
        value, pivot = states[mask]
        x = min(representatives[row] for row in representatives if pivot in row
                and minimum(remaining - row) == value - 1)
        suite.append(x); remaining -= incidence[x]
    return dict(kind='recurrence', suite=sorted(suite), root=sum(1 << i for i in universe),
                states=[[u, *states[u]] for u in sorted(states)], optimizer_states=len(states))


def support_families():
    for q in range(1, 4):
        for n in range(4):
            for family in itertools.product(range(1 << q), repeat=n):
                yield q, list(family)
    rng = random.Random(20261008)
    for _ in range(100):
        q = rng.randint(4, 7)
        yield q, [rng.randrange(1 << q) for _ in range(rng.randint(0, 8))]


def local_case(identifier, policies, q):
    mutations = []
    for s, policy in enumerate(policies):
        for rule in range(len(policy['rules'])):
            for op in ('flip', 'delete'):
                mutations.append(dict(id=f's{s}/r{rule:02d}/{op}', snapshot=s, rule=rule, op=op))
    return dict(id=identifier, requests=[[x] for x in range(q)], policies=policies,
                profile='local', mutations=mutations)


class SparseTransposeTests(unittest.TestCase):
    def test_complete_certificates_against_subset_reference(self):
        with patch.object(optimize.time, 'monotonic', return_value=0):
            for q, supports in support_families():
                self.assertEqual(optimize.dynamic_certificate({'requests': list(range(q))}, supports),
                                 reference(q, supports))

    def test_first_representative_and_original_mutation_positions(self):
        supports = [0, 0b0101, 0b1010, 0b0101, 0, 0b1111]
        with patch.object(optimize.time, 'monotonic', return_value=0):
            actual = optimize.dynamic_certificate({'requests': list(range(4))}, supports)
        self.assertEqual(actual, reference(4, supports))
        self.assertEqual(actual['suite'], [0, 1])
        self.assertEqual(actual['root'], 0b101110)

    def test_clipped_bits_and_negative_integer_direct_calls(self):
        # The old q-row construction ignored bits outside q, even on direct calls.
        for supports in ([0b10001, 0b10010], [-1, 0], [-2, 1]):
            with patch.object(optimize.time, 'monotonic', return_value=0):
                self.assertEqual(optimize.dynamic_certificate({'requests': [0, 1]}, supports),
                                 reference(2, supports))

    def test_exact_state_and_deadline_boundaries(self):
        case = {'requests': [0, 1]}; supports = [1, 2]
        with patch.object(optimize.time, 'monotonic', return_value=0):
            for cap in (0, 1, 2):
                with self.assertRaisesRegex(RuntimeError, 'exact solver.*budget exhausted'):
                    optimize.dynamic_certificate(case, supports, max_states=cap)
            self.assertEqual(optimize.dynamic_certificate(case, supports, max_states=3), reference(2, supports))
            self.assertEqual(optimize.dynamic_certificate(case, [0], max_states=0)['suite'], [])
            with self.assertRaisesRegex(RuntimeError, 'exact solver budget exhausted'):
                optimize.dynamic_certificate(case, supports, seconds=-1)
        with patch.object(optimize.time, 'monotonic', side_effect=[0, 1, 1]):
            self.assertEqual(optimize.dynamic_certificate(case, supports, seconds=1), reference(2, supports))
        with patch.object(optimize.time, 'monotonic', side_effect=[0, 1.01]):
            with self.assertRaisesRegex(RuntimeError, 'exact solver budget exhausted'):
                optimize.dynamic_certificate(case, supports, seconds=1)

    def test_real_policy_supports_checker_and_canonical_witness(self):
        cases = [local_case('triangle', [dict(combiner='FA', rules=[dict(effect='P', match='112'),
                    dict(effect='D', match='010'), dict(effect='P', match='111')]),
                    dict(combiner='FA', rules=[dict(effect='P', match='101')])], 3)]
        for alg in ('DO', 'PO', 'FA', 'ODO', 'OPO'):
            for tables in itertools.product(('000', '101', '112'), repeat=2):
                cases.append(local_case(alg + ''.join(tables), [dict(combiner=alg, rules=[
                    dict(effect='P', match=tables[0]), dict(effect='D', match=tables[1])])], 3))
        with patch.object(optimize.time, 'monotonic', return_value=0), \
             patch.object(optimize.time, 'process_time', return_value=0):
            for case in cases:
                independent, _ = checker.matrix(case)
                supports = [sum(1 << x for x in support) for support in independent]
                self.assertEqual(semantics.incidence(case)['supports'], supports)
                expected = reference(len(case['requests']), supports)
                for force in (False, True):
                    cert = optimize.optimize(case, force_dp=force)
                    self.assertTrue(checker.check(case, cert)['accepted'])
                    self.assertEqual(len(cert['suite']), len(expected['suite']))
                    if cert['kind'] == 'recurrence':
                        # Full-domain signatures may merge equal rows; check exact
                        # root values and complete recurrence with the unchanged checker.
                        self.assertEqual(next(v for u, v, _ in cert['states'] if u == cert['root']), len(expected['suite']))
                    bad = copy.deepcopy(cert); bad['suite'] = []
                    if any(supports):
                        missed = next(i for i, support in enumerate(independent) if support)
                        witness = checker.check(case, bad)
                        self.assertEqual(witness['mutation'], case['mutations'][missed]['id'])
                        self.assertEqual(witness['request_index'], min(independent[missed]))


if __name__ == '__main__':
    unittest.main()
