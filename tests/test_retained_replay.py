"""Portable finite replay of all owned inputs, without Linux resource claims."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import checker
from baselines import greedy
from generate import generate
from kernel_baseline import select
from optimize import optimize
from semantics import incidence


def stable(cert):
    return {k: v for k, v in cert.items() if k != 'cpu_seconds'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='new destination for actual per-case results and certificates')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'cases').mkdir()
    paths = sorted((ROOT / 'data' / 'cases').glob('*.json'))
    regenerated = {case['id']: case for case in generate()}
    if len(paths) != 144 or len(regenerated) != 144:
        raise ValueError('expected complete 144-case owned inventory')
    started = time.monotonic()
    totals = {'cases': 0, 'detectable': 0, 'equivalent': 0, 'packing': 0,
              'recurrence': 0, 'forced_recurrence_checks': 0,
              'greedy_excess': 0, 'kernel_greedy_excess': 0, 'checker_steps': 0,
              'linux_resource_guards_exercised': False}
    for path in paths:
        case_start = time.monotonic()
        case = json.loads(path.read_text(encoding='utf-8'))
        assert case == regenerated[case['id']]
        data = incidence(case)
        independent, steps = checker.matrix(case)
        assert independent == [{q for q in range(len(case['requests'])) if s >> q & 1}
                               for s in data['supports']]
        original = json.loads((ROOT / 'results/campaign/certificates' / path.name).read_text(encoding='utf-8'))
        certificate = optimize(case)
        forced = optimize(case, force_dp=True)
        outcomes = [checker.check(case, cert) for cert in (original, certificate, forced)]
        assert all(outcome['accepted'] for outcome in outcomes)
        assert stable(certificate) == stable(original)
        assert len(forced['suite']) == len(certificate['suite'])
        size = len(certificate['suite'])
        g = greedy(data['supports'], len(case['requests']))
        kernel = select(data['supports'], len(case['requests']))
        old_record = json.loads((ROOT / 'results/campaign/cases' / path.name).read_text(encoding='utf-8'))
        assert g == old_record['baseline']['greedy']['suite']
        record = {'id': case['id'], 'case': case, 'status': 'ok',
                  'supports': [sorted(s) for s in independent],
                  'certificate': certificate, 'forced_recurrence_certificate': forced,
                  'checker_outcomes': outcomes, 'greedy': g, 'kernel_greedy': kernel,
                  'wall_seconds': time.monotonic() - case_start}
        (args.output / 'cases' / path.name).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        totals['cases'] += 1
        totals['detectable'] += outcomes[1]['non_equivalent']
        totals['equivalent'] += outcomes[1]['equivalent']
        totals[certificate['kind']] += 1
        totals['forced_recurrence_checks'] += 1
        totals['greedy_excess'] += len(g) > size
        totals['kernel_greedy_excess'] += kernel['size'] > size
        totals['checker_steps'] += steps + sum(outcome['checker_steps'] for outcome in outcomes)
    assert (totals['cases'], totals['detectable'], totals['equivalent'],
            totals['packing'], totals['recurrence'], totals['greedy_excess'],
            totals['kernel_greedy_excess']) == (144, 3108, 1754, 111, 33, 32, 25)
    totals['wall_seconds'] = time.monotonic() - started
    (args.output / 'summary.json').write_text(json.dumps(totals, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(totals, sort_keys=True))


if __name__ == '__main__':
    main()
