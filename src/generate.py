"""Deterministic owned finite-policy corpus; never called public-policy data."""
from __future__ import annotations
import argparse, copy, itertools, json, random
from pathlib import Path
from semantics import local_mutations

SEED = 20260914

def requests(q):
    width=max(1,(q-1).bit_length())
    return [list(map(int,format(i,f'0{width}b'))) for i in range(q)]

def rule(effect, scope, q, errors=()):
    a=set(scope);e=set(errors)
    return {'effect':effect,'match':''.join('2' if x in e else '1' if x in a else '0' for x in range(q))}

def policy(alg,rs): return {'combiner':alg,'rules':rs}

def case(identifier,family,ps,q,extended=False,**metadata):
    return {'id':identifier,'family':family,'provenance':'owned generated finite input',
            'requests':requests(q),'policies':ps,'profile':'extended' if extended else 'local',
            'mutations':local_mutations(ps,extended),'metadata':metadata}

def partition(q,n,shuffle=None):
    xs=list(range(q))
    if shuffle is not None:shuffle.shuffle(xs)
    return [set(xs[i::n]) for i in range(n)]

def generate():
    result=[]
    for f in range(6):
        for i in range(20):
            seed=SEED+100*f+i;rng=random.Random(seed)
            identifier=f'generated-{20*f+i+1:03d}'
            if f in (0,1):
                q=32;dominant='D' if f==0 else 'P';subordinate='P' if f==0 else 'D'
                ps=[]
                for snapshot in range(2):
                    # A shuffled dyadic partition plus its ancestors is laminar;
                    # the common dominant mask preserves laminarity.
                    xs=list(range(q));rng.shuffle(xs)
                    scopes=[set(xs)]
                    for n in (2,4): scopes += [set(xs[j*q//n:(j+1)*q//n]) for j in range(n)]
                    rs=[rule(subordinate,s,q) for s in scopes]
                    rs += [rule(dominant,[x for x in range(q) if rng.random()<.12],q) for _ in range(2)]
                    rng.shuffle(rs)
                    ps.append(policy(('DO','ODO')[i%2] if f==0 else ('PO','OPO')[i%2],rs))
                result.append(case(identifier,'masked-deny' if f==0 else 'masked-permit',ps,q,seed=seed))
            elif f==2:
                q=32;n=4+i%7
                before=policy('FA',[rule(rng.choice('PD'),[x for x in range(q) if rng.random()<.22],q) for _ in range(n)])
                after=copy.deepcopy(before)
                if i%4==0:after['rules'][i%n]['effect']='D' if after['rules'][i%n]['effect']=='P' else 'P'
                elif i%4==1:after['rules'].reverse()
                elif i%4==2:after['rules'][i%n]['match']=rule('P',[x for x in range(q) if rng.random()<.35],q)['match']
                else:after['rules'].append(rule('D',[x for x in range(q) if x%3==i%3],q))
                result.append(case(identifier,'ordered-revision',[before,after],q,seed=seed,revision=i%4))
            elif f==3:
                q=32;n=i+2
                alg=('DO','PO','FA')[i%3]
                before=policy(alg,[rule('P',range(q),q) for _ in range(n)])
                after=policy(alg,[rule('P',s,q) for s in partition(q,n,rng)])
                result.append(case(identifier,'behavior-preserving',[before,after],q,seed=seed,blocks=n))
            elif f==4:
                q=16;ps=[]
                for s in range(2):
                    scopes=[{x for x in range(q) if rng.random()<.35} for _ in range(4+i%3)]
                    rs=[rule('P',t,q) for t in scopes for _ in range(2)]
                    ps.append(policy('DO',rs))
                result.append(case(identifier,'nonlaminar',[*ps],q,seed=seed))
            else:
                q=8;ps=[]
                for s in range(2):
                    rs=[]
                    for _ in range(3+i%3):
                        matches=''.join(rng.choices('012',weights=(5,4,1),k=q))
                        rs.append({'effect':rng.choice('PD'),'match':matches})
                    ps.append(policy(('DO','PO','FA')[(i+s)%3],rs))
                result.append(case(identifier,'typed-extended',ps,q,True,seed=seed))
    fs=[]
    def add(ps,q,extended=False,**meta):
        fs.append(case(f'fixture-{len(fs)+1:03d}','fixture',ps,q,extended,**meta))
    add([policy('DO',[]),policy('PO',[])],2,expected=0,phenomenon='empty obligations')
    add([policy('DO',[rule('P',range(4),4) for _ in range(3)])],4,expected=1,phenomenon='equivalent deletions')
    add([policy('DO',[rule('D',range(4),4),rule('P',range(4),4)])],4,expected=1,phenomenon='dominant masking')
    add([policy('FA',[rule('P',range(4),4),rule('D',range(4),4)])],4,expected=1,phenomenon='ordered shadowing')
    add([policy('DO',[rule('P',[0,1],4),rule('D',[1,2],4)]),policy('PO',[rule('P',[0,1],4),rule('D',[1,2],4)])],4,True,phenomenon='combiner revision')
    add([policy('DO',[rule('P',[],2,range(2))])],2,True,phenomenon='effect errors collapse only at root')
    add([policy('FA',[{'effect':'P','match':'112'}, {'effect':'P','match':'101'}, {'effect':'D','match':'010'}])],3,expected=1,phenomenon='incomparable error supports')
    triples=[(0,0,0),(0,1,1),(1,0,1),(1,1,0)]
    ps=[policy('DO',[rule('P',[i for i,t in enumerate(triples) if t[s]==v],4) for v in (0,1)]) for s in range(3)]
    add(ps,4,expected=3,phenomenon='three snapshot parity obstruction')
    for a,b in ((0,1),(0,2),(1,2)):add([ps[a],ps[b]],4,expected=2,phenomenon='two snapshot parity restriction')
    add([policy('DO',[rule('P',[0],2),rule('P',[1],2)]) for _ in range(3)],2,expected=2,phenomenon='three snapshot positive control')
    for n in (2,4,8,16):
        add([policy('DO',[rule('P',range(n),n) for _ in range(n)]),policy('DO',[rule('P',[i],n) for i in range(n)])],n,expected=n,phenomenon='unchanged output refinement',blocks=n)
    add([policy('DO',[rule('P',[0,1],3),rule('P',[2],3)]),policy('DO',[rule('P',[0,2],3),rule('P',[1],3)])],3,expected=2,expected_greedy=3,phenomenon='greedy loses an augmenting path')
    add([policy('DO',[rule('P',t,3) for t in ({0,1},{1,2},{0,2}) for _ in range(2)])],3,expected=2,phenomenon='triangle of mutation supports')
    add([policy('FA',[rule('P',[0],3)]),policy('FA',[rule('P',[0],3),rule('D',[1],3)])],3,expected=2,phenomenon='new request region')
    add([policy('DO',[rule('P',[0,1],4),rule('D',[2,3],4)]),policy('DO',[rule('D',[0,2],4),rule('P',[1,3],4)])],4,phenomenon='cross snapshot sharing')
    add([policy('DO',[rule('P',[0,1],4),rule('D',[1,2],4)]),policy('ODO',[rule('P',[0,1],4),rule('D',[1,2],4)])],4,True,phenomenon='decision equivalence of ordered overrides')
    add([policy('DO',[rule('P',[0,1],4),rule('P',[0,1],4)])],4,True,phenomenon='duplicate rule independence')
    add([policy('FA',[rule('P',[0,1],4),rule('D',[1,2],4),rule('P',range(4),4)])],4,True,phenomenon='adjacent rule ordering')
    add([policy('PO',[rule('P',[0],4,[1]),rule('D',[0,2],4,[3])]),policy('DO',[rule('P',[0],4,[1]),rule('D',[0,2],4,[3])])],4,True,phenomenon='typed error dominance')
    assert len(result)==120 and len(fs)==24
    return result+fs

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args()
    d=Path(a.output);d.mkdir(parents=True,exist_ok=True)
    for c in generate(): (d/(c['id']+'.json')).write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'owned_cases':144,'generated':120,'fixtures':24,'seed':SEED}))
if __name__=='__main__':main()
