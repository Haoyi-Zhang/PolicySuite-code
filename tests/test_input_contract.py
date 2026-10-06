"""Benign schema/profile regressions; no network or reference-result writes."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import checker
from semantics import local_mutations, validate
from optimize import optimize


def main():
    ps = [{'combiner': 'FA', 'rules': [{'effect': 'P', 'match': '1'}]}]
    base = {'id': 'input-contract', 'requests': [[0]], 'policies': ps,
            'profile': 'local', 'mutations': local_mutations(ps)}
    invalid = []
    for field, value in [('id', ''), ('requests', [0]), ('requests', [[]]),
                         ('requests', [[0.5]]), ('requests', [[True]]),
                         ('requests', [[0] * 13]), ('policies', [None]),
                         ('profile', 'unknown'), ('mutations', [None]),
                         ('mutations', base['mutations'][:1])]:
        case = copy.deepcopy(base)
        case[field] = value
        invalid.append(case)
    case = copy.deepcopy(base)
    case['requests'] = [[x] for x in range(9)]
    case['policies'][0]['rules'][0]['match'] = '1' * 9
    invalid.append(case)
    case = copy.deepcopy(base)
    case['requests'] = [[0], [1, 2]]
    case['policies'][0]['rules'][0]['match'] = '11'
    invalid.append(case)
    case = copy.deepcopy(base)
    case['profile'] = 'extended'
    case['mutations'] = local_mutations(case['policies'], True)[:-1]
    invalid.append(case)
    rejected = 0
    for case in invalid:
        for validator in (validate, checker.schema):
            try:
                validator(case)
            except ValueError:
                pass
            else:
                raise AssertionError('invalid input accepted')
        try:
            optimize(case)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('producer returned a certificate outside the input contract')
    valid = [copy.deepcopy(base)]
    declared = copy.deepcopy(base)
    declared['profile'] = 'declared'
    declared['mutations'] = declared['mutations'][:1]
    valid.append(declared)
    extended = copy.deepcopy(base)
    extended['profile'] = 'extended'
    extended['mutations'] = local_mutations(extended['policies'], True)
    valid.append(extended)
    mixed = copy.deepcopy(base)
    mixed['requests'] = [[1], ['1']]
    mixed['policies'][0]['rules'][0]['match'] = '11'
    valid.append(mixed)
    for case in valid:
        validate(case)
        checker.schema(case)
        assert checker.check(case, optimize(case))['accepted']
    print(json.dumps({'invalid_inputs_rejected_by_both': rejected,
                      'valid_profile_and_typed_atom_controls': len(valid)}))


if __name__ == '__main__':
    main()
