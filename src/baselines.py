"""Transparent in-house baselines on the identical finite candidate set."""
from __future__ import annotations
import itertools, random

def coverage(suite, supports):
    relevant=[s for s in supports if s]
    selected=sum(1<<x for x in set(suite))
    hits=sum(bool(s&selected) for s in relevant)
    return {'killed':hits,'detectable':len(relevant),'fraction':hits/len(relevant) if relevant else 1.0}

def greedy(supports,q):
    uncovered={i for i,s in enumerate(supports) if s};result=[]
    while uncovered:
        gains=[sum(bool(supports[i]>>x&1) for i in uncovered) for x in range(q)]
        x=max(range(q),key=lambda j:(gains[j],-j))
        if not gains[x]:raise ValueError('uncoverable nonempty support')
        result.append(x);uncovered={i for i in uncovered if not supports[i]>>x&1}
    return result

def pairwise(requests):
    dimensions=len(requests[0]);pairs=list(itertools.combinations(range(dimensions),2))
    # Single-dimensional inputs use value coverage; no invented Cartesian rows.
    targets=[{(i,j,q[i],q[j]) for i,j in pairs} if pairs else {(0,q[0])} for q in requests]
    remaining=set().union(*targets);result=[]
    while remaining:
        x=max(range(len(requests)),key=lambda j:(len(targets[j]&remaining),-j))
        if not targets[x]&remaining:raise ValueError('pairwise generation stalled')
        result.append(x);remaining-=targets[x]
    return result

def evaluate_baselines(case,data,optimum,repetitions=20):
    q=len(case['requests']);sup=data['supports']
    g=greedy(sup,q)
    activation=[]
    for p in case['policies']:
        activation.extend(sum(1<<x for x,v in enumerate(r['match']) if v=='1') for r in p['rules'])
    suites={'unreduced':list(range(q)),'greedy':g,'pairwise':pairwise(case['requests']),
            'conflict_oblivious':greedy(activation,q),
            'delta_only':[x for x in range(q) if len({o[x] for o in data['originals']})>1]}
    result={name:{'size':len(s),**coverage(s,sup),'suite':s} for name,s in suites.items()}
    base=20260914+sum((i+1)*ord(ch) for i,ch in enumerate(case['id']))
    trials=[]
    for trial in range(repetitions):
        order=list(range(q));random.Random(base+trial).shuffle(order)
        prefix=[]
        if any(sup):
            for x in order:
                prefix.append(x)
                if coverage(prefix,sup)['fraction']==1:break
        trials.append({'seed':base+trial,'complete_size':len(prefix),
                       'budget_size':optimum,'budget_fraction':coverage(order[:optimum],sup)['fraction']})
    result['random_trials']=trials
    return result
