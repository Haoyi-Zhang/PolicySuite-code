"""Read-only consistency audit for the retained output-preserving refinement data."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def derive():
    rows=[]
    for path in sorted((ROOT/'data/cases').glob('generated-*.json')):
        case=json.loads(path.read_text())
        if case['family']!='behavior-preserving':continue
        record=json.loads((ROOT/'results/campaign/cases'/path.name).read_text())
        alg=case['policies'][0]['combiner']
        expected_old=0 if alg=='PO' else 1
        if alg not in ('DO','PO','FA') or record['old_snapshot']['size']!=expected_old:
            raise ValueError('old minimum does not match declared combiner: '+case['id'])
        if record['optimum']!=case['metadata']['blocks'] or record['output_delta_requests']!=0:
            raise ValueError('common minimum/output delta mismatch: '+case['id'])
        rows.append({'case':case['id'],'combiner':alg,'old_minimum':expected_old,
                     'common_minimum':record['optimum'],'changed_output_requests':0})
    if len(rows)!=20:raise ValueError('expected all twenty refinement cases')
    return {'scope':'read-only reconciliation of retained records; no new experiment or changed inputs',
            'cases':rows,'old_minimum_one_cases':sum(r['old_minimum']==1 for r in rows),
            'old_minimum_zero_cases':sum(r['old_minimum']==0 for r in rows),
            'all_common_minima_equal_blocks':True,'all_output_deltas_empty':True}

if __name__=='__main__':
    expected=derive()
    if expected!=json.loads((ROOT/'results/refinement-audit.json').read_text()):
        raise SystemExit('Retained refinement interpretation differs from its raw cases.')
    print(json.dumps({'accepted':True,'one_to_n_cases':expected['old_minimum_one_cases'],
                      'zero_to_n_cases':expected['old_minimum_zero_cases']},sort_keys=True))
