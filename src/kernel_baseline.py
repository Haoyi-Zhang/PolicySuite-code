"""Post-protocol adversarial baseline: globally subsume supports before greedy.

This is a separate baseline, not a retuned exact solver or a preregistered
performance hypothesis. No optimizer or checker routines are imported.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from semantics import incidence

def select(supports, requests):
    unique = sorted(set(supports) - {0})
    kernel = [s for s in unique if not any(t != s and t & s == t for t in unique)]
    remaining = list(kernel); suite = []
    while remaining:
        q = max(range(requests), key=lambda x: (sum(bool(s & (1 << x)) for s in remaining), -x))
        suite.append(q); remaining = [s for s in remaining if not s & (1 << q)]
    detectable = sum(bool(s) for s in supports)
    mask = sum(1 << q for q in suite)
    killed = sum(bool(s & mask) for s in supports)
    if detectable != killed: raise RuntimeError('kernel baseline lost an obligation')
    return {'suite': suite, 'size': len(suite), 'detectable': detectable, 'killed': killed,
            'kernel_obligations': len(kernel)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cases', default='data/cases')
    ap.add_argument('--output', default='results/kernel-greedy.json'); args=ap.parse_args()
    start = time.process_time(); results=[]
    for p in sorted(Path(args.cases).glob('*.json')):
        c=json.loads(p.read_text()); result=select(incidence(c)['supports'],len(c['requests']))
        results.append(dict(id=c['id'],family=c['family'],**result))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'cases':results,'cpu_seconds':time.process_time()-start,
                              'classification':'post-protocol adversarial baseline'},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'cases':len(results),'cpu_seconds':time.process_time()-start}))
if __name__=='__main__': main()
