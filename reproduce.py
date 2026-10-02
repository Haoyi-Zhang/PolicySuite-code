#!/usr/bin/env python3
"""Clean, offline reproduction of retained finite evidence (Python standard library).

The output directory must not exist. Never overwrite the reference evidence.
Each child is run sequentially; no child process launches parallel workers.
"""
from __future__ import annotations
import argparse, csv, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOLATILE = {'cpu_seconds', 'wall_seconds', 'peak_rss_kib', 'certificate_bytes',
            'max_case_cpu_seconds', 'max_certificate_bytes'}

def normalized(x):
    if isinstance(x, dict):
        return {k: normalized(v) for k,v in x.items() if k not in VOLATILE}
    if isinstance(x, list):
        return [normalized(v) for v in x]
    return x

def same_json(a: Path, b: Path) -> None:
    if normalized(json.loads(a.read_text())) != normalized(json.loads(b.read_text())):
        raise ValueError(f'deterministic JSON mismatch: {a.name}')

def same_csv(a: Path, b: Path) -> None:
    with a.open(newline='') as fa, b.open(newline='') as fb:
        if normalized(list(csv.DictReader(fa))) != normalized(list(csv.DictReader(fb))):
            raise ValueError(f'deterministic CSV mismatch: {a.name}')

def command(args: list[str], save: Path | None = None) -> str:
    env = dict(os.environ, PYTHONHASHSEED='0', OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    run = subprocess.run([sys.executable, *args], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=45, check=True)
    if save is not None:
        value=json.loads(run.stdout)
        save.parent.mkdir(parents=True,exist_ok=True)
        save.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    return run.stdout

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,
                        help='new directory for regenerated evidence; must not exist')
    args=parser.parse_args(); out=args.output.resolve()
    if out.exists():
        raise SystemExit('Refusing an existing output directory. Choose a fresh path.')
    out.mkdir(parents=True)
    start=time.monotonic()
    report={'accepted':False, 'offline':True, 'workers':1,
            'excluded_nondeterministic_fields':sorted(VOLATILE)}
    try:
        command(['src/generate.py',str(out/'cases')])
        old=sorted((ROOT/'data/cases').glob('*.json'));new=sorted((out/'cases').glob('*.json'))
        if len(old)!=144 or [p.name for p in old]!=[p.name for p in new]:
            raise ValueError('owned-case inventory differs')
        for a,b in zip(old,new):
            # Inputs contain no timings and must be equal in full.
            if json.loads(a.read_text())!=json.loads(b.read_text()):
                raise ValueError(f'input differs: {a.name}')
        command(['tests/test_core.py'],out/'results/core-tests.json')
        command(['tests/test_structure.py'],out/'results/structure-tests.json')
        command(['tests/test_error_boundary.py'],out/'results/error-boundary-tests.json')
        # Verify exact retained proof-boundary inputs without rerunning the solver.
        sys.path.insert(0,str(ROOT/'tests'))
        from test_error_boundary import triangle
        for k in range(1,5):
            c=triangle(k)
            if c!=json.loads((ROOT/'data/proof-cases'/f'{c["id"]}.json').read_text()):
                raise ValueError('proof-boundary input differs')
        command(['src/run_campaign.py','--cases',str(out/'cases'),
                 '--output',str(out/'results/campaign'),'--start','0','--stop','144'])
        command(['src/kernel_baseline.py','--cases',str(out/'cases'),
                 '--output',str(out/'results/kernel-greedy.json')])
        command(['src/summarize.py','--results',str(out/'results'),
                 '--output',str(out/'results/derived')])
        count=0
        for folder in ('campaign/cases','campaign/certificates'):
            refs=sorted((ROOT/'results'/folder).glob('*.json'))
            fresh=sorted((out/'results'/folder).glob('*.json'))
            if [p.name for p in refs]!=[p.name for p in fresh]:raise ValueError('result inventory differs')
            for a,b in zip(refs,fresh):same_json(a,b);count+=1
        for name in ('core-tests.json','structure-tests.json','error-boundary-tests.json',
                     'kernel-greedy.json','campaign/summary.json','derived/totals.json'):
            same_json(ROOT/'results'/name,out/'results'/name);count+=1
        for name in ('campaign/metrics.csv','derived/families.csv','derived/coverage.csv','derived/amplification.csv'):
            same_csv(ROOT/'results'/name,out/'results'/name)
        summary=json.loads((out/'results/campaign/summary.json').read_text())
        report.update(accepted=True, owned_inputs_equal=144, proof_inputs_equal=4,
                      deterministic_json_outputs_equal=count, deterministic_csv_outputs_equal=4,
                      campaign_passed=summary['passed'], independently_coded_checker_used=True,
                      campaign_checker_steps_upper_bound=summary['checker_steps_upper_bound'],
                      campaign_cpu_seconds=summary['cpu_seconds'],
                      claim='retained finite reproducibility; not external review or a general mechanized proof')
    except (OSError,ValueError,subprocess.SubprocessError,AssertionError) as exc:
        report['error']=str(exc)
        if isinstance(exc,subprocess.CalledProcessError):
            report['child_stdout']=exc.stdout[-4000:]
            report['child_stderr']=exc.stderr[-4000:]
        raise
    finally:
        report['wall_seconds']=time.monotonic()-start
        (out/'reproduction.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
        print(json.dumps(report,sort_keys=True))

if __name__=='__main__':main()
