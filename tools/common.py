"""Shared, strict formula I/O for MATT v3. Source programs are never invoked."""
import bz2
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent
sys.path.insert(0,str(WORKSPACE/'envs'/'sat-core'/'Lib'/'site-packages'))
if (ROOT/'vendor'/'cnfgen').exists(): sys.path.insert(0,str(ROOT/'vendor'))
sys.path.insert(0,str(ROOT))
from generate import assignment_cost, serialize, xor, eq, exactly, atmost, evaluate


def sha(data): return hashlib.sha256(data).hexdigest()
def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def read_rows(path): return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
def write_rows(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='\n') as out:
        for row in rows: out.write(json.dumps(row,separators=(',',':'),ensure_ascii=False)+'\n')


def decode(data):
    if data.startswith(b'\xfd7zXZ'): data=lzma.decompress(data)
    elif data.startswith(b'\x1f\x8b'): data=gzip.decompress(data)
    elif data.startswith(b'BZh'): data=bz2.decompress(data)
    if len(data)>60_000_000: raise ValueError('Formula exceeds the release selection limit of 60 MB expanded')
    return data.decode('ascii')


def parse_text(text,expected=None):
    family=expected; nv=0; top=None; declared_count=None; hard=[]; soft=[]; pending=[]; comments=[]
    clauses=[]
    for line in text.splitlines():
        line=line.strip()
        if not line: continue
        if line.startswith('c'): comments.append(line); continue
        if line.startswith('%'): break
        if line.startswith('p '):
            tokens=line.split(); family=tokens[1]; nv=int(tokens[2]); declared_count=int(tokens[3])
            top=int(tokens[4]) if family=='wcnf' and len(tokens)>4 else None
            continue
        if family=='cnf':
            for tok in line.split():
                lit=int(tok)
                if lit==0: clauses.append(pending); pending=[]
                else: pending.append(lit)
        else:
            family='wcnf'; tokens=line.split()
            if tokens[-1]!='0': raise ValueError('Unterminated WCNF clause')
            weight=tokens[0]; clause=list(map(int,tokens[1:-1]))
            if weight=='h': hard.append(clause)
            else:
                w=int(weight)
                if w<=0: raise ValueError('Nonpositive soft weight')
                if top is not None and w>top: raise ValueError('Weight exceeds declared top')
                if top is not None and w==top: hard.append(clause)
                else: soft.append((w,clause))
    if pending: raise ValueError('Unterminated CNF clause')
    if family=='cnf': hard=clauses
    if declared_count is not None and declared_count!=len(hard)+len(soft): raise ValueError('Header clause count mismatch')
    used={abs(l) for c in hard+[c for _,c in soft] for l in c}
    observed=max(used,default=0)
    if nv and observed>nv: raise ValueError('Variable exceeds declared header')
    nv=max(nv,observed)
    if family not in ('cnf','wcnf') or not nv or not hard+soft: raise ValueError('Empty formula')
    for c in hard+[c for _,c in soft]:
        if not c: raise ValueError('Empty clause excluded from mathematical tier')
        if 0 in c: raise ValueError('Zero within clause')
    return nv,hard,soft,dict(comments=comments,original_top=top,used_variables=len(used),format=family)


def clean_for_math(h,s):
    for c in h+[c for _,c in s]:
        if len(c)!=len(set(c)) or any(-l in c for l in c): return False
    return True


def sat_truth(n,h,backbone=True,budget=100_000,time_budget=2):
    from pysat.solvers import Solver
    from threading import Timer
    with Solver(name='m22',bootstrap_with=h) as solver:
        timer=Timer(time_budget,solver.interrupt); timer.start()
        try:
            solver.conf_budget(budget); sat=solver.solve_limited(expect_interrupt=True)
            if sat is None: return dict(status='UNKNOWN',backbone=None,backbone_complete=False,label_evidence='local oracle budget exhausted')
            if not sat: return dict(status='UNSAT',backbone=None,backbone_complete=True,label_evidence='MiniSat22 UNSAT cross-check')
            raw={abs(l):l for l in solver.get_model()}; model=[raw.get(v,-v) for v in range(1,n+1)]
            result=dict(status='SAT',witness=model,backbone=None,backbone_complete=False,label_evidence='MiniSat22 checked witness')
            if backbone:
                bb=[]; complete=True
                for lit in model:
                    solver.conf_budget(budget); answer=solver.solve_limited(assumptions=[-lit],expect_interrupt=True)
                    if answer is False: bb.append(lit)
                    if answer is None: complete=False
                result.update(backbone=sorted(bb,key=abs),backbone_complete=complete)
            return result
        finally: timer.cancel()


def emit(rows,spec,index,variant,n,h,s,truth,parameters,source=None,relation=None,group_override=None):
    family=spec['family']; gid=group_override or f"{spec['id']}/{index:04d}"
    rel=f"instances/{family}/{spec['id']}/{index:04d}_{variant}.{family}"
    data=serialize(n,h,s,family); path=ROOT/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    seed=int(sha(f"20261016/v3/{gid}".encode())[:16],16)
    lineage=source.get('lineage_id',gid) if source else gid
    bucket=int(sha(lineage.encode())[:8],16)%10
    row=dict(id=f'{gid}/{variant}',group_id=gid,scenario_id=spec['id'],variant=variant,
        split='train' if bucket<6 else 'dev' if bucket<8 else 'test',path=rel,
        format='dimacs-cnf' if family=='cnf' else 'wcnf-old',sha256=sha(data),nvars=n,
        nclauses=len(h)+len(s),hard_clauses=len(h),soft_clauses=len(s),total_soft_weight=sum(w for w,_ in s),
        seed=seed,parameters=parameters,truth=truth,scenario=spec['scenario'],rationale=spec['rationale'],
        intervention=spec.get('intervention'),origin=spec.get('origin','constructed'),tier=spec.get('tier','extended'),
        label_evidence=truth.get('label_evidence','construction with independent validation'))
    if source: row['source']=source
    if relation: row['relation_to_control']=relation
    rows.append(row)
    return row


def scenario(sid,family,title,scenario_text,rationale,intervention='',**extra):
    return dict(id=sid,family=family,title=title,scenario=scenario_text,rationale=rationale,
                intervention=intervention,targets=['A','D'] if family=='cnf' else ['B','C'],**extra)
