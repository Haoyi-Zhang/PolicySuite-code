"""Connect the existing public-error theorem domain to the production entry.

Owned finite tables only; no native-language or external PDP validation.
"""
import copy
import itertools
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import checker
import semantics
import optimize
from test_error_boundary import brute, local_packing


def case(rules, q=3):
    policies=[{'combiner':'FA','rules':rules}]
    return {'id':'owned-fa-control','requests':[[x] for x in range(q)],
            'policies':policies,'profile':'local',
            'mutations':semantics.local_mutations(policies)}


class FaConstructorTests(unittest.TestCase):
    def test_existing_2971_theorem_cases_use_production_constructor(self):
        choices=[{'effect':e,'match':''.join(t)} for e in 'PD'
                 for t in itertools.product('012',repeat=3)]
        checked=0
        for n in range(3):
            for rules in itertools.product(choices,repeat=n):
                c=case(list(rules))
                supports,_=checker.matrix(c)
                expected=local_packing(c,supports)
                actual=optimize.optimize(c,fa_local=True)
                self.assertEqual(actual['kind'],'packing')
                self.assertEqual(actual['optimizer_states'],0)
                self.assertEqual(len(actual['suite']),brute(supports,3))
                self.assertEqual(len(actual['suite']),len(expected['suite']))
                self.assertTrue(checker.check(c,actual)['accepted'])
                checked+=1
        self.assertEqual(checked,2971)

    def test_retained_incomparable_error_fixture_and_ordinary_exact_null(self):
        c=json.loads((ROOT/'data/cases/fixture-007.json').read_text(encoding='utf-8'))
        ordinary=optimize.optimize(c,force_dp=True)
        old=optimize.optimize(c)
        constructive=optimize.optimize(c,fa_local=True)
        self.assertEqual((old['kind'],old['optimizer_states']),('recurrence',3))
        self.assertEqual((constructive['kind'],constructive['optimizer_states']),('packing',0))
        self.assertEqual((ordinary['suite'],constructive['suite']),([1],[1]))
        self.assertTrue(checker.check(c,constructive)['accepted'])

    def test_disjoint_flip_delete_and_separate_visible_groups(self):
        c=case([{'effect':'P','match':'120'}, {'effect':'D','match':'001'},
                {'effect':'P','match':'110'}])
        supports,_=checker.matrix(c)
        constructive=optimize.optimize(c,fa_local=True)
        self.assertEqual(constructive['suite'],[0,1,2])
        self.assertEqual(len(constructive['packing']),3)
        self.assertEqual(brute(supports,3),3)
        self.assertTrue(checker.check(c,constructive)['accepted'])

    def test_zero_obligations_and_joint_quotient_lifting(self):
        for rules, expected in (([],[]),([{'effect':'P','match':'111'}],[0]),
                                ([{'effect':'D','match':'222'}],[0])):
            c=case(rules)
            actual=optimize.optimize(c,fa_local=True)
            self.assertEqual(actual['suite'],expected)
            self.assertEqual(actual['request_regions'],1)
            self.assertTrue(checker.check(c,actual)['accepted'])

    def test_explicit_scope_and_profile_guards(self):
        base=case([{'effect':'P','match':'112'}])
        for transform in ('two-snapshots','overrides','declared','extended','omission'):
            c=copy.deepcopy(base)
            if transform=='two-snapshots': c['policies'].append(copy.deepcopy(c['policies'][0]))
            elif transform=='overrides': c['policies'][0]['combiner']='DO'
            elif transform=='declared': c['profile']='declared'
            elif transform=='extended': c['profile']='extended'
            if transform=='omission': c['mutations'].pop()
            else: c['mutations']=semantics.local_mutations(c['policies'],c['profile']=='extended')
            with self.assertRaises(ValueError): optimize.optimize(c,fa_local=True)
        with self.assertRaises(ValueError): optimize.optimize(base,force_dp=True,fa_local=True)

    def test_independent_checker_and_canonical_uncovered_witness_unchanged(self):
        c=json.loads((ROOT/'data/cases/fixture-007.json').read_text(encoding='utf-8'))
        cert=optimize.optimize(c,fa_local=True)
        bad=copy.deepcopy(cert);bad['suite']=[]
        result=checker.check(c,bad)
        self.assertEqual((result['accepted'],result['mutation'],result['request_index']),
                         (False,'s0/r00/flip',0))
        self.assertEqual((result['reference'],result['mutant']),('P','D'))
        bad=copy.deepcopy(cert);bad['suite']=[0,2]
        bad['packing']=['s0/r00/flip','s0/r00/delete']
        with self.assertRaisesRegex(checker.Invalid,'overlapping packing supports'):
            checker.check(c,bad)


if __name__=='__main__': unittest.main()
