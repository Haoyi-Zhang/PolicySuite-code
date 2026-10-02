"""Exhaustive finite checks; these are not machine-checked general proofs."""
from __future__ import annotations
import copy, itertools, json, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import checker
from semantics import incidence, evaluate, local_mutations
from optimize import optimize

def brute(supports, q):
    nonzero = [s for s in supports if s]
    for k in range(q+1):
        for choices in itertools.combinations(range(q),k):
            mask = sum(1 << x for x in choices)
            if all(mask & s for s in nonzero): return k
    raise AssertionError('finite cover must exist')

def make_case(identifier, ps, q, extended=False):
    return {'id':identifier,'requests':[[x] for x in range(q)],'policies':ps,
            'profile':'extended' if extended else 'local','mutations':local_mutations(ps,extended)}

def main():
    start = time.process_time(); counts = {'scalar_policies':0,'finite_exact_cases':0,'corruptions_rejected':0}
    # Every length <= 4 list of valid flat rule outcomes, all five combiners.
    outcomes = [('P','0'),('P','1'),('D','1'),('P','2'),('D','2')]
    for n in range(5):
        for vector in itertools.product(outcomes,repeat=n):
            for alg in ('DO','PO','FA','ODO','OPO'):
                p = {'combiner':alg,'rules':[{'effect':e,'match':m} for e,m in vector]}
                assert evaluate(p,1)[0] == checker.decision(p,0)
                counts['scalar_policies'] += 1
    # All q=2 ternary target vectors, both effects, <= 2 rules, all algorithms.
    choices = [{'effect':e,'match':''.join(v)} for e in ('P','D') for v in itertools.product('012',repeat=2)]
    for n in range(3):
        for vector in itertools.product(choices,repeat=n):
            for alg in ('DO','PO','FA','ODO','OPO'):
                c = make_case('tiny', [{'combiner':alg,'rules':list(vector)}],2,True)
                data = incidence(c); independent,_ = checker.matrix(c)
                assert independent == [set(x for x in range(2) if s >> x & 1) for s in data['supports']]
                answer = optimize(c); assert checker.check(c,answer)['accepted']
                assert len(answer['suite']) == brute(data['supports'],2)
                counts['finite_exact_cases'] += 1
    # Non-laminar error fixture requires complete recurrence, not a fake packing.
    p = {'combiner':'FA','rules':[{'effect':'P','match':'112'},
        {'effect':'P','match':'101'}, {'effect':'D','match':'010'}]}
    c = make_case('error-overlap',[p],3)
    cert = optimize(c,True); assert checker.check(c,cert)['accepted']
    bads = []
    bad = copy.deepcopy(cert); bad['suite']=[]; bads.append(bad)
    bad = copy.deepcopy(cert); bad['equivalent']=['invented']; bads.append(bad)
    bad = copy.deepcopy(cert); bad['states'][-1][1] += 1; bads.append(bad)
    bad = copy.deepcopy(cert); bad['states']=bad['states'][1:]; bads.append(bad)
    bad = copy.deepcopy(cert); bad['suite'].append(bad['suite'][0]); bads.append(bad)
    for bad in bads:
        try: rejected = not checker.check(c,bad)['accepted']
        except checker.Invalid: rejected = True
        assert rejected; counts['corruptions_rejected'] += 1
    bad_case=copy.deepcopy(c);bad_case['mutations'].pop()
    try: checker.check(bad_case,cert)
    except checker.Invalid: counts['corruptions_rejected'] += 1
    else: raise AssertionError('incomplete mutation profile accepted')
    counts['cpu_seconds'] = time.process_time() - start
    print(json.dumps(counts,sort_keys=True))

if __name__ == '__main__': main()
