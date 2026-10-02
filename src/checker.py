"""Small, separately implemented finite-policy certificate checker.

This module intentionally imports neither semantics nor optimize. It recomputes
all observations from the case, checks the declared mutation profile, and checks
a packing lower bound or a full finite recurrence. It is not an XACML PDP.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

class Invalid(ValueError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise Invalid(message)

def schema(c: Any) -> None:
    require(isinstance(c, dict), 'case is not an object')
    require(isinstance(c.get('id'), str) and bool(c['id']), 'missing case id')
    qs = c.get('requests')
    require(isinstance(qs, list) and 1 <= len(qs) <= 4096, 'request bound')
    require(all(isinstance(q, list) and 1 <= len(q) <= 12 for q in qs), 'request tuple shape')
    require(len({len(q) for q in qs}) == 1, 'inconsistent tuple dimensions')
    require(all(all(type(v) in (int, str) for v in q) for q in qs), 'request atom type')
    require(len({json.dumps(q, sort_keys=True) for q in qs}) == len(qs), 'duplicate request')
    require(all(len({json.dumps(q[i]) for q in qs}) <= 8 for i in range(len(qs[0]))), 'attribute-domain bound')
    ps = c.get('policies')
    require(isinstance(ps, list) and 1 <= len(ps) <= 3, 'snapshot bound')
    for p in ps:
        require(isinstance(p, dict) and p.get('combiner') in ('DO','PO','FA','ODO','OPO'), 'combiner')
        rs = p.get('rules')
        require(isinstance(rs, list) and len(rs) <= 80, 'rule bound')
        for r in rs:
            require(isinstance(r, dict) and r.get('effect') in ('P','D'), 'rule effect')
            require(isinstance(r.get('match'), str) and len(r['match']) == len(qs)
                    and all(x in '012' for x in r['match']), 'rule match table')
    ms = c.get('mutations')
    require(isinstance(ms, list) and len(ms) <= 256, 'mutation bound')
    seen = set()
    for m in ms:
        require(isinstance(m, dict) and isinstance(m.get('id'), str) and m['id'] not in seen, 'mutation identifier')
        seen.add(m['id'])
        s = m.get('snapshot')
        require(type(s) is int and 0 <= s < len(ps), 'mutation snapshot')
        op = m.get('op')
        require(op in ('flip','delete','true','false','swap','combiner'), 'mutation operator')
        if op == 'combiner':
            require(m.get('value') in ('DO','PO','FA','ODO','OPO'), 'replacement combiner')
        else:
            i = m.get('rule')
            require(type(i) is int and 0 <= i < len(ps[s]['rules']), 'mutation rule')
            if op == 'swap':
                require(i + 1 < len(ps[s]['rules']), 'swap endpoint')
    # The profile is an enforceable completeness contract, not a label supplied
    # by the optimizer. Custom ablations are allowed only under "declared".
    profile = c.get('profile')
    require(profile in ('local','extended','declared'), 'unknown mutation profile')
    if profile != 'declared':
        expected = []
        for s, p in enumerate(ps):
            for i in range(len(p['rules'])):
                for op in (['flip','delete'] if profile == 'local' else ['flip','delete','true','false']):
                    expected.append({'id':f's{s}/r{i:02d}/{op}', 'snapshot':s, 'rule':i, 'op':op})
            if profile == 'extended':
                for a in ['DO','PO','FA']:
                    if a != p['combiner']:
                        expected.append({'id':f's{s}/combiner/{a}', 'snapshot':s, 'op':'combiner','value':a})
                for i in range(len(p['rules']) - 1):
                    expected.append({'id':f's{s}/r{i:02d}/swap','snapshot':s,'rule':i,'op':'swap'})
        require(ms == expected, 'incomplete or altered declared mutation profile')

def decision(p: dict, q: int, mutation: dict | None = None) -> str:
    """Independent interpreter: edit rule positions on demand, no cloned policy."""
    alg = p['combiner']
    if mutation is not None and mutation['op'] == 'combiner':
        alg = mutation['value']
    values = []
    for position in range(len(p['rules'])):
        index = position
        if mutation is not None and mutation['op'] == 'swap':
            j = mutation['rule']
            if position == j: index = j + 1
            elif position == j + 1: index = j
        if mutation is not None and mutation['op'] == 'delete' and index == mutation['rule']:
            continue
        rule = p['rules'][index]
        active, effect = rule['match'][q], rule['effect']
        if mutation is not None and mutation['op'] != 'combiner' and index == mutation['rule']:
            if mutation['op'] == 'flip': effect = 'D' if effect == 'P' else 'P'
            elif mutation['op'] == 'true': active = '1'
            elif mutation['op'] == 'false': active = '0'
        values.append('N' if active == '0' else effect if active == '1' else ('IP' if effect == 'P' else 'ID'))
    if alg == 'FA':
        out = 'N'
        for v in values:
            if v != 'N': out = v; break
    else:
        counts = {s: values.count(s) for s in ('N','P','D','IP','ID','IDP')}
        if alg in ('DO','ODO'):
            if counts['D']: out = 'D'
            elif counts['IDP'] or (counts['ID'] and (counts['IP'] or counts['P'])): out = 'IDP'
            elif counts['ID']: out = 'ID'
            elif counts['P']: out = 'P'
            elif counts['IP']: out = 'IP'
            else: out = 'N'
        else:
            if counts['P']: out = 'P'
            elif counts['IDP'] or (counts['IP'] and (counts['ID'] or counts['D'])): out = 'IDP'
            elif counts['IP']: out = 'IP'
            elif counts['D']: out = 'D'
            elif counts['ID']: out = 'ID'
            else: out = 'N'
    return 'I' if out.startswith('I') else out

def matrix(c: dict) -> tuple[list[set[int]], int]:
    schema(c)
    originals = [[decision(p, q) for q in range(len(c['requests']))] for p in c['policies']]
    supports = []
    steps = sum(len(p['rules']) * len(c['requests']) for p in c['policies'])
    for m in c['mutations']:
        p = c['policies'][m['snapshot']]
        supports.append({q for q in range(len(c['requests'])) if decision(p,q,m) != originals[m['snapshot']][q]})
        steps += len(p['rules']) * len(c['requests'])
    return supports, steps

def check(c: dict, cert: Any) -> dict:
    supports, steps = matrix(c)
    require(isinstance(cert, dict), 'certificate is not an object')
    require(cert.get('case_id') == c['id'], 'case binding')
    suite = cert.get('suite')
    require(isinstance(suite, list) and all(type(q) is int and 0 <= q < len(c['requests']) for q in suite), 'suite index')
    require(len(set(suite)) == len(suite), 'duplicate suite request')
    equivalent = [m['id'] for m, s in zip(c['mutations'], supports) if not s]
    require(cert.get('equivalent') == equivalent, 'incorrect equivalent-mutation inventory')
    selected = set(suite)
    for m, s in zip(c['mutations'], supports):
        if s and not s & selected:
            q = min(s)
            return {'accepted':False,'reason':'uncovered mutation','mutation':m['id'],
                    'request_index':q,'request':c['requests'][q],
                    'reference':decision(c['policies'][m['snapshot']],q),
                    'mutant':decision(c['policies'][m['snapshot']],q,m),
                    'checker_steps':steps}
    if cert.get('kind') == 'packing':
        packing = cert.get('packing')
        require(isinstance(packing, list) and all(isinstance(x,str) for x in packing), 'packing type')
        require(len(set(packing)) == len(packing) == len(suite), 'packing cardinality')
        lookup = {m['id']:s for m,s in zip(c['mutations'],supports)}
        union = set()
        for identifier in packing:
            require(identifier in lookup and bool(lookup[identifier]), 'packing member')
            require(not (union & lookup[identifier]), 'overlapping packing supports')
            union.update(lookup[identifier]); steps += len(lookup[identifier])
    elif cert.get('kind') == 'recurrence':
        full = sum(1 << i for i, s in enumerate(supports) if s)
        require(type(cert.get('root')) is int and cert['root'] == full, 'recurrence root')
        raw = cert.get('states')
        require(isinstance(raw, list) and 1 <= len(raw) <= 100000, 'recurrence size')
        states = {}
        for item in raw:
            require(isinstance(item,list) and len(item)==3 and all(type(x) is int for x in item), 'recurrence state type')
            u, value, pivot = item
            require(u >= 0 and u & ~full == 0 and u not in states and 0 <= value <= len(c['requests']), 'invalid recurrence state')
            states[u] = (value,pivot)
        require(states.get(0) == (0,-1) and full in states, 'missing base/root state')
        rows = [sum(1 << i for i,s in enumerate(supports) if q in s) for q in range(len(c['requests']))]
        for u, (value,pivot) in states.items():
            if not u: continue
            require(0 <= pivot < len(supports) and u & (1 << pivot) != 0, 'recurrence pivot')
            children = {u & ~rows[q] for q in supports[pivot]}
            require(bool(children) and all(v in states and v != u for v in children), 'missing recurrence child')
            require(value == 1 + min(states[v][0] for v in children), 'incorrect recurrence value')
            steps += len(supports[pivot])
        require(states[full][0] == len(suite), 'root lower bound differs from suite')
    else:
        raise Invalid('unknown certificate kind')
    return {'accepted':True,'case':c['id'],'minimum_size':len(suite),'kind':cert['kind'],
            'non_equivalent':sum(bool(s) for s in supports),'equivalent':len(equivalent),'checker_steps':steps}

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('case'); ap.add_argument('certificate')
    args = ap.parse_args()
    try:
        c = json.loads(Path(args.case).read_text())
        cert = json.loads(Path(args.certificate).read_text())
        result = check(c,cert)
    except (Invalid, ValueError, KeyError, TypeError, OSError, RecursionError) as e:
        result = {'accepted':False,'reason':str(e)}
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result['accepted'] else 2)

if __name__ == '__main__': main()
