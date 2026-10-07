"""Exact selection: two disjoint-minimum layers, otherwise a bounded DP proof.
No approximation is labeled optimal. Deadlines/state exhaustion raise errors.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from semantics import incidence

def bits(x:int):
    while x:
        b=x&-x;yield b.bit_length()-1;x-=b

def minimal_indices(supports:list[int],indices:list[int])->list[int]:
    # A duplicate support retains the first declared obligation.
    unique={}
    for i in indices:
        if supports[i]:unique.setdefault(supports[i],i)
    vals=sorted(unique,key=lambda x:(x.bit_count(),x))
    mins=[]
    for s in vals:
        if not any(t&s==t for t in mins):mins.append(s)
    return [unique[s] for s in mins]

def matching_certificate(case:dict,supports:list[int]):
    if len(case['policies'])>2:return None
    layers=[]
    for s in range(len(case['policies'])):
        a=minimal_indices(supports,[i for i,m in enumerate(case['mutations']) if m['snapshot']==s])
        union=0
        for i in a:
            if union&supports[i]:return None
            union|=supports[i]
        layers.append(a)
    while len(layers)<2:layers.append([])
    A,B=layers;adj=[[j for j,b in enumerate(B) if supports[a]&supports[b]] for a in A]
    right={}
    def aug(i,seen):
        for j in adj[i]:
            if j in seen:continue
            seen.add(j)
            if j not in right or aug(right[j],seen):right[j]=i;return True
        return False
    for i in range(len(A)):aug(i,set())
    left={i:j for j,i in right.items()}
    zl={i for i in range(len(A)) if i not in left};zr=set();queue=list(sorted(zl))
    while queue:
        i=queue.pop()
        for j in adj[i]:
            if left.get(i)==j or j in zr:continue
            zr.add(j)
            if j in right and right[j] not in zl:zl.add(right[j]);queue.append(right[j])
    pack=[A[i] for i in sorted(zl)]+[B[j] for j in range(len(B)) if j not in zr]
    suite=[next(bits(supports[A[i]]&supports[B[j]])) for j,i in sorted(right.items())]
    suite += [next(bits(supports[A[i]])) for i in range(len(A)) if i not in left]
    suite += [next(bits(supports[B[j]])) for j in range(len(B)) if j not in right]
    if len(set(suite))!=len(suite):raise RuntimeError('edge-cover construction invariant')
    return dict(kind='packing',suite=sorted(suite),packing=[case['mutations'][i]['id'] for i in pack],
                matching_size=len(right),layer_blocks=[len(A),len(B)],optimizer_states=0)

def dynamic_certificate(case:dict,supports:list[int],max_states:int=100000,seconds:float=60):
    q=len(case['requests']);n=len(supports)
    rows=[0]*q
    request_mask=(1<<q)-1
    for i,s in enumerate(supports):
        # Only the declared q request positions were inspected by the dense loop.
        for x in bits(s & request_mask):rows[x] |= 1<<i
    full=sum(1<<i for i,s in enumerate(supports) if s)
    candidates={}
    for x,r in enumerate(rows):
        if r:candidates.setdefault(r,x)
    coverers={i:[r for r in candidates if r>>i&1] for i in bits(full)}
    dp={0:(0,-1)};deadline=time.monotonic()+seconds
    def solve(u):
        if u in dp:return dp[u][0]
        if len(dp)>=max_states or time.monotonic()>deadline:raise RuntimeError('exact solver budget exhausted')
        pivot=min(bits(u),key=lambda i:(len(coverers[i]),i))
        children=sorted({u&~r for r in coverers[pivot]},key=lambda v:(v.bit_count(),v))
        value=1+min(solve(v) for v in children)
        if len(dp)>=max_states:raise RuntimeError('exact solver state budget exhausted')
        dp[u]=(value,pivot);return value
    optimum=solve(full);u=full;suite=[]
    while u:
        k,p=dp[u]
        chosen=min((candidates[r],r) for r in coverers[p] if dp[u&~r][0]==k-1)
        suite.append(chosen[0]);u &= ~chosen[1]
    return dict(kind='recurrence',suite=sorted(suite),root=full,states=[[u,*dp[u]] for u in sorted(dp)],optimizer_states=len(dp))

def optimize(case:dict,force_dp=False)->dict:
    t=time.process_time();a=incidence(case);supports=a['supports']
    representatives=[region[0] for region in a['regions']]
    reduced=dict(case, requests=[case['requests'][x] for x in representatives])
    projected=[sum(1<<j for j,x in enumerate(representatives) if s>>x&1) for s in supports]
    cert=None if force_dp else matching_certificate(reduced,projected)
    if cert is None:cert=dynamic_certificate(reduced,projected)
    cert['suite']=sorted(representatives[x] for x in cert['suite'])
    cert.update(case_id=case['id'],equivalent=[m['id'] for m,s in zip(case['mutations'],supports) if not s],
                cpu_seconds=time.process_time()-t,request_regions=len(a['regions']))
    return cert

def main():
    ap=argparse.ArgumentParser();ap.add_argument('case');ap.add_argument('output');ap.add_argument('--force-dp',action='store_true');a=ap.parse_args()
    case=json.loads(Path(a.case).read_text());cert=optimize(case,a.force_dp)
    Path(a.output).write_text(json.dumps(cert,indent=2)+'\n')
    print(json.dumps(dict(case=case['id'],size=len(cert['suite']),kind=cert['kind'])))
if __name__=='__main__':main()
