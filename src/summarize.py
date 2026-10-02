"""Derive every quantitative paper table and plot datum from retained records."""
from __future__ import annotations
import argparse,csv,json,statistics
from pathlib import Path

def write_csv(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def derive(root):
    rows=[json.loads(p.read_text()) for p in sorted((root/'campaign/cases').glob('*.json'))]
    if len(rows)!=144 or any(r['status']!='ok' for r in rows):raise ValueError('expected all 144 successful cases')
    kg={r['id']:r for r in json.loads((root/'kernel-greedy.json').read_text())['cases']}
    families=['masked-deny','masked-permit','ordered-revision','behavior-preserving','nonlaminar','typed-extended','fixture']
    family_rows=[];cov_rows=[]
    for index,fam in enumerate(families,1):
        rs=[r for r in rows if r['family']==fam]
        family_rows.append(dict(family=fam,cases=len(rs),q_min=min(r['requests'] for r in rs),q_max=max(r['requests'] for r in rs),
          rules_min=min(r['max_rules_per_snapshot'] for r in rs),rules_max=max(r['max_rules_per_snapshot'] for r in rs),
          mutations_min=min(r['mutations'] for r in rs),mutations_max=max(r['mutations'] for r in rs),
          detectable=sum(r['detectable'] for r in rs),equivalent=sum(r['equivalent'] for r in rs),
          optimum_min=min(r['optimum'] for r in rs),optimum_max=max(r['optimum'] for r in rs),
          packing=sum(r['certificate']=='packing' for r in rs),
          greedy_excess_cases=sum(r['baseline']['greedy']['size']>r['optimum'] for r in rs),
          kernel_excess_cases=sum(kg[r['id']]['size']>r['optimum'] for r in rs),
          mean_optimum=statistics.mean(r['optimum'] for r in rs),
          mean_greedy=statistics.mean(r['baseline']['greedy']['size'] for r in rs),
          mean_kernel=statistics.mean(kg[r['id']]['size'] for r in rs),
          mean_random_complete=statistics.mean(t['complete_size'] for r in rs for t in r['baseline']['random_trials']),
          cpu_seconds=sum(r['cpu_seconds'] for r in rs)))
        cov_rows.append(dict(index=index,family=fam,
          pairwise=statistics.mean(r['baseline']['pairwise']['fraction'] for r in rs),
          conflict_oblivious=statistics.mean(r['baseline']['conflict_oblivious']['fraction'] for r in rs),
          delta_only=statistics.mean(r['baseline']['delta_only']['fraction'] for r in rs),
          random_at_optimum=statistics.mean(t['budget_fraction'] for r in rs for t in r['baseline']['random_trials']),
          flip_only=statistics.mean(r['ablations']['flip']['full_profile_coverage'] for r in rs),
          delete_only=statistics.mean(r['ablations']['delete']['full_profile_coverage'] for r in rs),
          local_only=statistics.mean(r['ablations']['local']['full_profile_coverage'] for r in rs),
          old_only=statistics.mean(r['old_snapshot']['common_coverage'] for r in rs)))
    amp=[dict(blocks=r['optimum'],old_size=r['old_snapshot']['size'],common_size=r['optimum'],delta_requests=r['output_delta_requests']) for r in rows if r['family']=='behavior-preserving']
    totals=dict(cases=len(rows),mutations=sum(r['mutations'] for r in rows),detectable=sum(r['detectable'] for r in rows),
      equivalent=sum(r['equivalent'] for r in rows),greedy_excess_cases=sum(r['baseline']['greedy']['size']>r['optimum'] for r in rows),
      kernel_excess_cases=sum(kg[r['id']]['size']>r['optimum'] for r in rows),
      max_case_cpu_seconds=max(r['cpu_seconds'] for r in rows),max_states=max(r['states'] for r in rows),
      max_case_encoding_bytes=max(r['case_encoding_bytes'] for r in rows),max_certificate_bytes=max(r['certificate_bytes'] for r in rows))
    return family_rows,cov_rows,amp,totals

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',default='results');ap.add_argument('--output',default='results/derived');a=ap.parse_args()
    f,c,amp,t=derive(Path(a.results));out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'families.csv',f);write_csv(out/'coverage.csv',c);write_csv(out/'amplification.csv',amp)
    (out/'totals.json').write_text(json.dumps(t,indent=2,sort_keys=True)+'\n')
    print(json.dumps(t,sort_keys=True))
if __name__=='__main__':main()
