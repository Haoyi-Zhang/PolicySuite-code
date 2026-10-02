"""Finite flat-policy semantics. No network, production PDP, or external solver.
Ternary rule matches: 0=false, 1=true, 2=error. Public observations collapse
extended Indeterminate to I only after the root combiner has run.
"""
from __future__ import annotations
from typing import Any

ALGORITHMS = ('DO', 'PO', 'FA', 'ODO', 'OPO')

def validate(case: dict[str, Any]) -> None:
    if not isinstance(case, dict) or not isinstance(case.get('id'), str):
        raise ValueError('case must have a string id')
    req = case.get('requests')
    if not isinstance(req, list) or not 1 <= len(req) <= 4096:
        raise ValueError('request count outside 1..4096')
    if len({repr(x) for x in req}) != len(req):
        raise ValueError('duplicate requests')
    ps = case.get('policies')
    if not isinstance(ps, list) or not 1 <= len(ps) <= 3:
        raise ValueError('expected one to three snapshots')
    for p in ps:
        if p.get('combiner') not in ALGORITHMS or not isinstance(p.get('rules'),list) or len(p['rules'])>80:
            raise ValueError('invalid policy')
        for r in p['rules']:
            if r.get('effect') not in ('P','D') or not isinstance(r.get('match'),str) or len(r['match'])!=len(req) or set(r['match'])-set('012'):
                raise ValueError('invalid finite rule match table')
    muts=case.get('mutations')
    if not isinstance(muts,list) or len(muts)>256:raise ValueError('mutation limit')
    ids=[]
    for m in muts:
        if not isinstance(m.get('id'),str):raise ValueError('mutation id')
        ids.append(m['id']);s=m.get('snapshot')
        if type(s) is not int or not 0<=s<len(ps):raise ValueError('snapshot index')
        if m.get('op') not in ('flip','delete','true','false','swap','combiner'):raise ValueError('mutation operation')
        if m['op']=='combiner':
            if m.get('value') not in ALGORITHMS:raise ValueError('mutation combiner')
        else:
            i=m.get('rule')
            if type(i) is not int or not 0<=i<len(ps[s]['rules']):raise ValueError('rule index')
            if m['op']=='swap' and i+1>=len(ps[s]['rules']):raise ValueError('swap endpoint')
    if len(set(ids))!=len(ids):raise ValueError('duplicate mutation ids')

def mutate(p:dict,m:dict)->dict:
    p={'combiner':p['combiner'],'rules':[dict(r) for r in p['rules']]};op=m['op']
    if op=='combiner':p['combiner']=m['value'];return p
    i=m['rule']
    if op=='delete':p['rules'].pop(i)
    elif op=='flip':p['rules'][i]['effect']='D' if p['rules'][i]['effect']=='P' else 'P'
    elif op in ('true','false'):p['rules'][i]['match']=('1' if op=='true' else '0')*len(p['rules'][i]['match'])
    elif op=='swap':p['rules'][i],p['rules'][i+1]=p['rules'][i+1],p['rules'][i]
    return p

def combine(v:list[str],alg:str)->str:
    if alg=='FA':return next((x for x in v if x!='N'),'N')
    if alg in ('PO','OPO'):
        swap={'P':'D','D':'P','IP':'ID','ID':'IP','IDP':'IDP','N':'N'}
        return swap[combine([swap[x] for x in v],'DO')]
    s=set(v)
    if 'D' in s:return 'D'
    if 'IDP' in s:return 'IDP'
    if 'ID' in s and ('IP' in s or 'P' in s):return 'IDP'
    if 'ID' in s:return 'ID'
    if 'P' in s:return 'P'
    if 'IP' in s:return 'IP'
    return 'N'

def evaluate(p:dict,q:int)->list[str]:
    out=[]
    for x in range(q):
        v=[('N' if r['match'][x]=='0' else r['effect'] if r['match'][x]=='1' else 'I'+r['effect']) for r in p['rules']]
        d=combine(v,p['combiner']);out.append('I' if d.startswith('I') else d)
    return out

def incidence(case:dict)->dict:
    validate(case);q=len(case['requests'])
    originals=[evaluate(p,q) for p in case['policies']]
    supports=[];mutant_outputs=[]
    for m in case['mutations']:
        s=m['snapshot'];o=evaluate(mutate(case['policies'][s],m),q)
        supports.append(sum(1<<x for x in range(q) if originals[s][x]!=o[x]))
        mutant_outputs.append(o)
    # Quotient by complete rule-match signatures. All declared operations
    # preserve this partition, including globally true/false targets.
    signatures={};regions=[]
    for x in range(q):
        sig=tuple(r['match'][x] for p in case['policies'] for r in p['rules'])
        if sig not in signatures:signatures[sig]=len(regions);regions.append([])
        regions[signatures[sig]].append(x)
    return dict(supports=supports,originals=originals,mutants=mutant_outputs,regions=regions)

def local_mutations(policies:list[dict],extended:bool=False)->list[dict]:
    out=[]
    for s,p in enumerate(policies):
        for i in range(len(p['rules'])):
            for op in (('flip','delete','true','false') if extended else ('flip','delete')):
                out.append(dict(id=f's{s}/r{i:02d}/{op}',snapshot=s,rule=i,op=op))
        if extended:
            for alg in ('DO','PO','FA'):
                if alg!=p['combiner']:out.append(dict(id=f's{s}/combiner/{alg}',snapshot=s,op='combiner',value=alg))
            for i in range(len(p['rules'])-1):
                out.append(dict(id=f's{s}/r{i:02d}/swap',snapshot=s,rule=i,op='swap'))
    if len(out)>256:raise ValueError('declared family exceeds mutation cap')
    return out
