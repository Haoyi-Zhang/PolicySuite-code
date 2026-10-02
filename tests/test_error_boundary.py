"""Additional proof validation: full public-error FA and a sharp packing gap.

These are separate theorem tests, not additional public benchmark policies.
"""
from __future__ import annotations
import itertools, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import checker
from semantics import local_mutations
from optimize import optimize

def local_packing(case, supports):
    """At most two supports per visible rule; select their common point or both."""
    suite=[]; packing=[]
    for i in range(len(case['policies'][0]['rules'])):
        ids=[j for j,m in enumerate(case['mutations']) if m.get('rule')==i and supports[j]]
        if len(ids)==2 and supports[ids[0]] & supports[ids[1]]:
            suite.append(min(supports[ids[0]] & supports[ids[1]]));packing.append(case['mutations'][ids[0]]['id'])
        else:
            for j in ids: suite.append(min(supports[j]));packing.append(case['mutations'][j]['id'])
    return {'case_id':case['id'],'kind':'packing','suite':suite,'packing':packing,
            'equivalent':[m['id'] for m,s in zip(case['mutations'],supports) if not s]}

def brute(supports,q):
    supports=[s for s in supports if s]
    for k in range(q+1):
        for t in itertools.combinations(range(q),k):
            if all(set(t)&s for s in supports):return k
    raise RuntimeError('finite coverage unexpectedly impossible')

def packing_opt(supports):
    supports=list({tuple(sorted(s)) for s in supports if s});best=0
    def search(i,used,count):
        nonlocal best
        if count+len(supports)-i<=best:return
        if i==len(supports):best=max(best,count);return
        s=set(supports[i])
        if not used&s:search(i+1,used|s,count+1)
        search(i+1,used,count)
    search(0,set(),0);return best

def triangle(k):
    q=3*k
    def table(a,b):return ''.join('1' if j in a else '2' if j in b else '0' for j in range(q))
    left=[];right=[]
    for i in range(k):
        a,b,c=3*i,3*i+1,3*i+2
        left.extend([{'effect':'P','match':table({a,b},{c})},
                     {'effect':'D','match':table({b},set())},
                     {'effect':'P','match':table({a,b,c},set())}])
        right.append({'effect':'P','match':table({a,c},set())})
    ps=[{'combiner':'FA','rules':left},{'combiner':'FA','rules':right}]
    return {'id':f'error-triangle-{k:02d}','family':'proof-boundary',
            'profile':'local','requests':[[j//4,j%4] for j in range(q)],
            'policies':ps,'mutations':local_mutations(ps),
            'metadata':{'expected':2*k,'expected_packing':k,'provenance':'owned theorem construction'}}

def main():
    start=time.process_time();count=0;steps=0
    choices=[{'effect':e,'match':''.join(t)} for e in 'PD' for t in itertools.product('012',repeat=3)]
    for n in range(3):
        for rs in itertools.product(choices,repeat=n):
            ps=[{'combiner':'FA','rules':list(rs)}]
            c={'id':'finite-fa-error','profile':'local','requests':[[0],[1],[2]],
               'policies':ps,'mutations':local_mutations(ps)}
            supports,s=checker.matrix(c);steps+=s
            cert=local_packing(c,supports);v=checker.check(c,cert);steps+=v['checker_steps']
            assert v['accepted'] and v['minimum_size']==brute(supports,3)
            count+=1
    cases=[]
    for k in range(1,5):
        c=triangle(k);supports,s=checker.matrix(c);steps+=s
        cert=optimize(c);v=checker.check(c,cert);steps+=v['checker_steps']
        assert v['accepted'] and v['minimum_size']==brute(supports,3*k)==2*k
        p=packing_opt(supports);assert p==k
        cases.append({'blocks':k,'requests':3*k,'optimum':2*k,'maximum_packing':p})
    print(json.dumps({'single_snapshot_cases':count,'sharp_gap_cases':cases,
                      'checker_steps':steps,'cpu_seconds':time.process_time()-start},indent=2,sort_keys=True))
if __name__=='__main__':main()
