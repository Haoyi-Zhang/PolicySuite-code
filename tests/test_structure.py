"""Independent exhaustive error-free structural and matching oracle."""
import itertools,time,resource,json
start=time.process_time()
def ev(rules,alg,x):
    vals=[e for t,e in rules if x in t]
    if alg=='FA': return vals[0] if vals else 'N'
    hi='D' if alg=='DO' else 'P';lo='P' if hi=='D' else 'D'
    return hi if hi in vals else lo if lo in vals else 'N'
def supports(rules,alg,q):
    orig=[ev(rules,alg,x) for x in range(q)];out=[]
    for i,(t,e) in enumerate(rules):
        for op in ('flip','delete'):
            r=list(rules)
            if op=='flip':r[i]=(t,'D' if e=='P' else 'P')
            else:r.pop(i)
            d=frozenset(x for x in range(q) if orig[x]!=ev(r,alg,x))
            if d:out.append(d)
    return out
def minimal(f):
    return sorted([s for s in set(f) if not any(t<s for t in f)],key=lambda s:tuple(sorted(s)))
def lam(f):
    return all(not(a&b) or a<=b or b<=a for a,b in itertools.combinations(f,2))
def disjoint(f):return all(not(a&b) for a,b in itertools.combinations(f,2))
def match(A,B):
    adj=[[j for j,b in enumerate(B) if a&b] for a in A]; mt={}
    def aug(i,seen):
        for j in adj[i]:
            if j in seen:continue
            seen.add(j)
            if j not in mt or aug(mt[j],seen):mt[j]=i;return True
        return False
    for i in range(len(A)):aug(i,set())
    return len(mt)
def oracle(f,q):
    for k in range(q+1):
        for x in itertools.combinations(range(q),k):
            if all(set(x)&s for s in f):return k
q=3;sub=[frozenset(x for x in range(q) if m>>x&1) for m in range(1<<q)]
checked=0;admitted=0
for n in range(4):
 for r in itertools.product(list(itertools.product(sub,('P','D'))),repeat=n):
  for alg in ('DO','PO','FA'):
   f=supports(r,alg,q);hi='D' if alg=='DO' else 'P'
   mask=frozenset().union(*(t for t,e in r if e==hi))
   premise=alg=='FA' or lam([t-mask for t,e in r if e!=hi])
   if premise:
    assert disjoint(minimal(f)),(r,alg,f)
    assert oracle(f,q)==len(minimal(f))
    admitted+=1
   checked+=1
q=4;S=[frozenset(x for x in range(q) if m>>x&1) for m in range(1,1<<q)]
fams=[()]
for k in range(1,q+1):
 fams += [f for f in itertools.combinations(S,k) if disjoint(f)]
pairs=0
for A in fams:
 for B in fams:
    v=len(A)+len(B)-match(A,B)
    assert v==oracle(A+B,q),(A,B,v)
    pairs+=1
triples=[(0,0,0),(0,1,1),(1,0,1),(1,1,0)]
f=[frozenset(i for i,t in enumerate(triples) if t[d]==v) for d in range(3) for v in range(2)]
assert oracle(f,4)==3
assert all(oracle(f[2*i:2*i+2]+f[2*j:2*j+2],4)==2 for i,j in itertools.combinations(range(3),2))
res=dict(policy_evaluations=checked,structural_admissions=admitted,two_layer_families=len(fams),two_layer_pairs=pairs,three_layer_control_optimum=3,cpu_seconds=time.process_time()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,workers=1)
print(json.dumps(res,indent=2))
