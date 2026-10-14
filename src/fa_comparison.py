"""Paired complete finite-workflow costs on unchanged owned eligible cases.

The ordinary exact baseline is the existing generic recurrence, not an
independent external solver. Both routes get the same full table/inventory and
joint quotient; the unchanged independently coded checker recomputes supports.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

import checker
from optimize import optimize
from semantics import incidence

ROOT=Path(__file__).resolve().parents[1]


def write_new(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as h:
        h.write(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')


def eligible(c):
    return (c['profile']=='local' and len(c['policies'])==1
            and c['policies'][0]['combiner']=='FA')


def trial(path, mode, wire_path):
    phases={}
    started=(time.perf_counter(),time.process_time())
    def stage(name, action):
        w,c=time.perf_counter(),time.process_time()
        try:
            return action()
        finally:
            phases[name]={'wall_seconds':time.perf_counter()-w,'cpu_seconds':time.process_time()-c}
    cert=None;verdict=None;wire=None;error=None
    try:
        c=stage('input_read_parse',lambda:json.loads(path.read_text(encoding='utf-8')))
        cert=stage('produce',lambda:optimize(c,force_dp=mode=='ordinary',fa_local=mode=='fa-local'))
        def wire_roundtrip():
            raw=(json.dumps(cert,sort_keys=True,allow_nan=False)+'\n').encode('utf-8')
            with wire_path.open('xb') as h:
                h.write(raw)
            return raw,json.loads(wire_path.read_text(encoding='utf-8'))
        wire,decoded=stage('certificate_write_read_parse',wire_roundtrip)
        verdict=stage('independent_check',lambda:checker.check(c,decoded))
        if not verdict['accepted']:
            raise RuntimeError('certificate rejected')
    except (ValueError,RuntimeError,RecursionError,OSError,MemoryError) as exc:
        error={'type':type(exc).__name__,'message':str(exc)}
    total={'wall_seconds':time.perf_counter()-started[0],
           'cpu_seconds':time.process_time()-started[1]}
    return {'mode':mode,'status':'ok' if error is None else 'failed',
            'phases':phases,'total':total,'certificate':cert,'verdict':verdict,'error':error,
            'certificate_bytes':len(wire) if wire is not None else None,
            'wire_sha256':sha256(wire).hexdigest() if wire is not None else None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cases',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=5)
    args=p.parse_args()
    if not 1<=args.repeats<=7: p.error('repeats must be in 1..7')
    work,out=args.work.resolve(),args.out.resolve()
    if work==out or work in out.parents or out in work.parents:
        p.error('work and evidence directories must be disjoint')
    work.mkdir(parents=True,exist_ok=False)
    out.mkdir(parents=True,exist_ok=False)
    rows=[];scope=[];summary=[];failures=0
    for path in sorted(args.cases.glob('*.json')):
        raw=path.read_bytes();c=json.loads(raw)
        include=eligible(c)
        scope.append({'path':path.name,'id':c['id'],'input_sha256':sha256(raw).hexdigest(),
                      'eligible':include,'reason':'one FA, complete local' if include else 'outside constructor scope'})
        if not include: continue
        # Audit same information independently, outside repeated timing samples.
        data=incidence(c);independent,_=checker.matrix(c)
        agree=independent==[{q for q in range(len(c['requests'])) if support>>q&1}
                            for support in data['supports']]
        if not agree: raise RuntimeError('independent support audit differs')
        samples=[]
        for repeat in range(args.repeats):
            order=('ordinary','fa-local') if repeat%2==0 else ('fa-local','ordinary')
            for mode in order:
                result=trial(path,mode,work/f'{path.stem}-{repeat}-{mode}.json')
                result.update(case_id=c['id'],repeat=repeat,order=list(order))
                rows.append(result);samples.append(result)
                failures+=result['status']!='ok'
        per_mode={mode:[r for r in samples if r['mode']==mode and r['status']=='ok']
                  for mode in ('ordinary','fa-local')}
        sizes={mode:sorted({len(r['certificate']['suite']) for r in values})
               for mode,values in per_mode.items()}
        same_size=(sizes['ordinary']==sizes['fa-local'] and len(sizes['ordinary'])==1
                   and all(len(v)==args.repeats for v in per_mode.values()))
        failures+=not same_size
        stats={mode:{'median_total_wall_seconds':statistics.median(r['total']['wall_seconds'] for r in values),
                     'median_total_cpu_seconds':statistics.median(r['total']['cpu_seconds'] for r in values),
                     'median_produce_cpu_seconds':statistics.median(r['phases']['produce']['cpu_seconds'] for r in values),
                     'median_check_cpu_seconds':statistics.median(r['phases']['independent_check']['cpu_seconds'] for r in values),
                     'proof_kinds':sorted({r['certificate']['kind'] for r in values}),
                     'optimizer_states':sorted({r['certificate']['optimizer_states'] for r in values}),
                     'checker_steps':sorted({r['verdict']['checker_steps'] for r in values})}
               for mode,values in per_mode.items() if values}
        summary.append({'id':c['id'],'requests':len(c['requests']),
                        'rules':len(c['policies'][0]['rules']),'mutations':len(c['mutations']),
                        'same_optimum':same_size,'sizes':sizes,'costs':stats})
        write_new(out/(path.stem+'.json'),{'case':c,'input_sha256':sha256(raw).hexdigest(),
                  'full_supports':data['supports'],'independent_supports':[sorted(s) for s in independent],
                  'same_information_verified':agree,'samples':samples})
    sources=('src/fa_comparison.py','src/optimize.py','src/semantics.py','src/checker.py')
    write_new(out/'bindings.json',{'source_sha256':{f:sha256((ROOT/f).read_bytes()).hexdigest() for f in sources},
                'environment':{'python':sys.version,'platform':platform.platform(),'executable':sys.executable,
                               'PYTHONDONTWRITEBYTECODE':os.environ.get('PYTHONDONTWRITEBYTECODE'),
                               'bytecode_disabled':sys.dont_write_bytecode},
                'command':[sys.executable,'-B',str(Path(__file__).resolve()),*sys.argv[1:]]})
    result={'format':'policy-fa-comparison-1','input_scope':scope,'eligible_cases':len(summary),
            'cases':summary,'trial_count':len(rows),'failed_trials_or_pairs':failures,
            'ordinary_baseline':'same-code generic exact recurrence, same supports and joint quotient; not external solver',
            'cost_scope':'warm in-process input read/parse, producer including semantics and quotient, certificate file roundtrip, independent checker; excludes imports/process startup, experiment packaging and native policy execution',
            'memory_measurement':None,'native_validation':False,'speedup_claim':False}
    write_new(out/'summary.json',result)
    print(json.dumps({'eligible_cases':len(summary),'trials':len(rows),'failures':failures},sort_keys=True))
    return 0 if failures==0 and summary else 1


if __name__=='__main__': raise SystemExit(main())
