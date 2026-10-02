"""Bounded, resumable finite validation. One process, no network or subprocesses."""
from __future__ import annotations
import argparse, copy, csv, json, resource, signal, time
from pathlib import Path
import checker
from semantics import incidence
from optimize import optimize
from baselines import coverage, evaluate_baselines

def atomic(path, value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');tmp.replace(path)

def timeout_handler(signum, frame):
    raise TimeoutError('whole-case 60-second limit')

def rejected(c, cert):
    try:return not checker.check(c,cert)['accepted']
    except checker.Invalid:return True

def run(c):
    begin=time.process_time();wall=time.monotonic()
    data=incidence(c);cert=optimize(c)
    checked=checker.check(c,cert)
    if not checked['accepted']:raise RuntimeError('exact certificate rejected: '+str(checked))
    q=len(c['requests']);steps=checked['checker_steps']
    expected=c.get('metadata',{}).get('expected')
    if expected is not None and len(cert['suite'])!=expected:raise RuntimeError('fixture expected optimum disagrees')
    b=evaluate_baselines(c,data,len(cert['suite']))
    eg=c.get('metadata',{}).get('expected_greedy')
    if eg is not None and b['greedy']['size']!=eg:raise RuntimeError('greedy fixture disagrees')
    # Changed profile is explicitly declared, not incorrectly labeled complete.
    ablations={}
    for label,ops in [('flip',{'flip'}),('delete',{'delete'}),('local',{'flip','delete'})]:
        a=copy.deepcopy(c);a['profile']='declared';a['mutations']=[m for m in a['mutations'] if m['op'] in ops]
        ac=optimize(a);v=checker.check(a,ac)
        if not v['accepted']:raise RuntimeError('ablation certificate rejected')
        steps+=v['checker_steps']
        ablations[label]={'size':len(ac['suite']),'full_profile_coverage':coverage(ac['suite'],data['supports'])['fraction']}
    old=copy.deepcopy(c);old['profile']='declared';old['policies']=old['policies'][:1];old['mutations']=[m for m in old['mutations'] if m['snapshot']==0]
    oc=optimize(old);ov=checker.check(old,oc);steps+=ov['checker_steps']
    if not ov['accepted']:raise RuntimeError('old-snapshot certificate rejected')
    old_info={'size':len(oc['suite']),'common_coverage':coverage(oc['suite'],data['supports'])['fraction'],'suite':oc['suite']}
    # A minimum suite minus any selected member must expose an uncovered mutant.
    corruptions=[]
    if cert['suite']:
        bad=copy.deepcopy(cert);bad['suite']=bad['suite'][1:]
        result=checker.check(c,bad);steps+=result['checker_steps']
        if result['accepted'] or result.get('reason')!='uncovered mutation':raise RuntimeError('missing-test control did not expose a witness')
        corruptions.append({'type':'remove_selected_request','rejected':True,'witness':result})
    # Proof mutations are tested only on the fixed fixtures to bound rechecking.
    if c['family']=='fixture':
        bads=[]
        bad=copy.deepcopy(cert);bad['equivalent']=['not-a-mutation'];bads.append(('equivalent_inventory',bad))
        bad=copy.deepcopy(cert);bad['kind']='unknown';bads.append(('unknown_proof',bad))
        if cert['kind']=='packing' and cert['packing']:
            bad=copy.deepcopy(cert);bad['packing'].append(bad['packing'][0]);bads.append(('duplicate_packing',bad))
        elif cert['kind']=='recurrence':
            bad=copy.deepcopy(cert)
            for row in bad['states']:
                if row[0]==bad['root']:row[1]+=1
            bads.append(('wrong_recurrence_value',bad))
            bad=copy.deepcopy(cert);bad['states']=[row for row in bad['states'] if row[0]!=0];bads.append(('missing_recurrence_base',bad))
        for name,bad in bads:
            if not rejected(c,bad):raise RuntimeError('corruption accepted: '+name)
            # Conservative bound: charge every rule visit and proof edge from
            # the valid proof, even when malformed data causes earlier exit.
            steps+=checked['checker_steps']
            corruptions.append({'type':name,'rejected':True})
    width=max((s.bit_length() for s in data['supports']),default=0)
    record={'id':c['id'],'family':c['family'],'status':'ok','requests':q,
      'snapshots':len(c['policies']),'rules':sum(len(p['rules']) for p in c['policies']),
      'max_rules_per_snapshot':max(len(p['rules']) for p in c['policies']),
      'mutations':len(c['mutations']),'detectable':checked['non_equivalent'],'equivalent':checked['equivalent'],
      'regions':len(data['regions']),'optimum':len(cert['suite']),'certificate':cert['kind'],
      'states':cert['optimizer_states'],'support_bit_width':width,
      'case_encoding_bytes':len(json.dumps(c,sort_keys=True).encode()),
      'certificate_bytes':len(json.dumps(cert,sort_keys=True).encode()),
      'output_delta_requests':len(b['delta_only']['suite']),
      'baseline':b,'ablations':ablations,'old_snapshot':old_info,'corruptions':corruptions,
      'checker_steps_upper_bound':steps,'cpu_seconds':time.process_time()-begin,
      'wall_seconds':time.monotonic()-wall,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    if record['wall_seconds']>60:raise RuntimeError('case time limit')
    return record,cert

def summary(records):
    ok=[r for r in records if r['status']=='ok']
    return {'case_count':len(records),'passed':len(ok),'failed':len(records)-len(ok),
       'cpu_seconds':sum(r.get('cpu_seconds',0) for r in records),
       'peak_rss_kib':max((r.get('peak_rss_kib',0) for r in records),default=0),
       'checker_steps_upper_bound':sum(r.get('checker_steps_upper_bound',0) for r in records),
       'main_recurrence_states':sum(r.get('states',0) for r in ok),
       'main_request_regions':sum(r.get('regions',0) for r in ok),
       'packing_cases':sum(r['certificate']=='packing' for r in ok),
       'recurrence_cases':sum(r['certificate']=='recurrence' for r in ok),
       'corruptions_rejected':sum(len(r['corruptions']) for r in ok),
       'workers':1,'random_repetitions':20}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cases',default='data/cases');ap.add_argument('--output',default='results/campaign')
    ap.add_argument('--start',type=int,default=0);ap.add_argument('--stop',type=int,default=144);ap.add_argument('--resume',action='store_true')
    args=ap.parse_args();paths=sorted(Path(args.cases).glob('*.json'))
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True);(out/'certificates').mkdir(exist_ok=True);(out/'cases').mkdir(exist_ok=True)
    signal.signal(signal.SIGALRM,timeout_handler)
    # Address-space guard is above the observed standard-library demand and
    # below the project RAM ceiling. No swap is configured or requested here.
    resource.setrlimit(resource.RLIMIT_AS,(int(2.75*1024**3),int(2.75*1024**3)))
    for path in paths[args.start:args.stop]:
        result_path=out/'cases'/path.name;cert_path=out/'certificates'/path.name
        if args.resume and result_path.exists() and cert_path.exists():continue
        c=json.loads(path.read_text());start=time.process_time();signal.alarm(60)
        try:
            result,cert=run(c);atomic(cert_path,cert)
        except (ValueError,RuntimeError,TimeoutError,MemoryError,RecursionError) as e:
            result={'id':c.get('id',path.stem),'family':c.get('family'),'status':'failed','error':str(e),'cpu_seconds':time.process_time()-start}
        finally:signal.alarm(0)
        atomic(result_path,result)
    records=[json.loads(p.read_text()) for p in sorted((out/'cases').glob('*.json'))]
    totals=summary(records);atomic(out/'summary.json',totals)
    with (out/'metrics.csv').open('w',newline='') as f:
        columns=['id','family','status','requests','snapshots','rules','mutations','detectable','equivalent','regions','optimum','certificate','states','cpu_seconds','wall_seconds','peak_rss_kib','checker_steps_upper_bound']
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(records)
    print(json.dumps(totals,sort_keys=True))
    if totals['failed']:raise SystemExit(2)

if __name__=='__main__':main()
