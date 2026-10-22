"""Audit the MATT data without running any A/B/C/D baseline.

python verify.py --pysat-path ../envs/sat-core/Lib/site-packages
The optional PySAT path enables independent MiniSat22 SAT/backbone and RC2/Glucose3
optimization checks of EVERY file. Without it, use --pysat to use installed PySAT.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

from generate import ROOT, assignment_cost, dump, evaluate, model_from_index


def parse(path):
    lines=path.read_text(encoding="ascii").splitlines()
    header=lines[0].split(); assert header[:1]==["p"]
    family=header[1]; n=int(header[2]); count=int(header[3]); top=int(header[4]) if family=="wcnf" else None
    assert family in ("cnf","wcnf") and n>0 and len(lines)-1==count
    h=[]; s=[]
    for line in lines[1:]:
        tokens=list(map(int,line.split())); assert tokens[-1]==0
        if family=="wcnf": w=tokens.pop(0); assert 0<w<=top
        clause=tokens[:-1]
        assert clause and all(1<=abs(l)<=n for l in clause)
        assert len(set(clause))==len(clause) and not any(-l in clause for l in clause)
        if family=="cnf" or w==top: h.append(clause)
        else: s.append((w,clause))
    assert {abs(l) for c in h+[c for _,c in s] for l in c}==set(range(1,n+1))
    if top is not None: assert top==sum(w for w,_ in s)+1 and s
    return n,h,s


def scalar_truth(n,h,s):
    """Simple assignment-by-assignment independent reference for a small audit sample."""
    count=0; forced=set(range(-n,n+1))-{0}; best=None; opt_count=0
    for idx in range(1<<n):
        model=model_from_index(idx,n); cost=assignment_cost(model,h,s)
        if cost is None: continue
        count+=1; forced.intersection_update(model)
        if best is None or cost<best: best=cost; opt_count=1
        elif cost==best: opt_count+=1
    result={"model_count":count,"backbone":sorted(forced,key=abs) if count else None,
            "status":"OPTIMUM" if count and s else "SAT" if count else "UNSAT"}
    if count and s: result.update(optimum=best,optimal_model_count=opt_count)
    return result


def canonical(h,s):
    return (sorted(tuple(sorted(c)) for c in h),sorted((w,tuple(sorted(c))) for w,c in s))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--pysat",action="store_true")
    ap.add_argument("--pysat-path",type=Path)
    args=ap.parse_args(); root=args.root.resolve(); started=time.time()
    use_pysat=args.pysat or bool(args.pysat_path)
    if args.pysat_path: sys.path.insert(0,str(args.pysat_path.resolve()))
    if use_pysat:
        import pysat
        from pysat.solvers import Solver
        from pysat.formula import WCNF
        from pysat.examples.rc2 import RC2
    rows=[json.loads(l) for l in (root/"manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    scenarios=json.loads((root/"scenarios.json").read_text(encoding="utf-8"))["scenarios"]
    ids=set(); hashes=set(); formulas=set(); parsed={}; groups={}; scalar_scenarios=set()
    stats=Counter(); family_stats=Counter()
    for pos,row in enumerate(rows):
        path=(root/row["path"]).resolve(); assert path.is_relative_to(root/"instances")
        data=path.read_bytes(); assert hashlib.sha256(data).hexdigest()==row["sha256"]
        assert row["id"] not in ids and row["sha256"] not in hashes
        ids.add(row["id"]); hashes.add(row["sha256"])
        n,h,s=parse(path); assert n==row["nvars"] and len(h)+len(s)==row["nclauses"]
        key=(n,str(canonical(h,s))); assert key not in formulas; formulas.add(key)
        truth=evaluate(n,h,s); assert truth==row["truth"],row["id"]
        if truth["status"]!="UNSAT":
            assert assignment_cost(truth["witness"],h,s)==truth.get("optimum",0)
        if row["scenario_id"] not in scalar_scenarios and n<=14:
            scalar=scalar_truth(n,h,s)
            assert all(truth[k]==v for k,v in scalar.items()),row["id"]
            scalar_scenarios.add(row["scenario_id"]); stats["scalar_full_enumeration_files"]+=1
        if "suboptimal_trap" in row:
            trap=row["suboptimal_trap"]; actual=assignment_cost(trap["assignment"],h,s)
            assert actual==trap["cost"]>truth["optimum"]
            neighbors=[assignment_cost([-l if abs(l)==v else l for l in trap["assignment"]],h,s) for v in range(1,n+1)]
            assert neighbors==trap["one_flip_costs"] and all(c is None or c>=actual for c in neighbors)
            assert all(c is None or c>actual for c in neighbors[:row["parameters"]["core_nvars"]])
            stats["suboptimal_trap_certificates"]+=1
        # Check construction-specific mathematical invariants, independently of descriptions.
        sid=row["scenario_id"]; variant=row["variant"]; p=row["parameters"]
        if variant!="disguised":
            if sid in ("ferromagnetic_barrier","feasible_exchange_barrier") and variant=="challenge": assert truth["optimum"]==p["B"]
            if sid=="weighted_parity_frustration": assert truth["optimum"]==(0 if variant=="control" else min(p["edge_weights"]))
            if sid=="last_soft_conflict": assert truth["optimum"]==(0 if variant=="control" else min(p["weights"]))
            if sid=="vertex_cover_star": assert truth["optimum"]==min(sum(p["leaf_weights"]),p["center_costs"][variant=="challenge"])
            if sid=="conjunction_trigger": assert truth["optimum"]==p["cheap_cost" if variant=="control" else "triggered_cost"]
            if sid=="cost_component_bridge" and variant=="control": assert truth["optimum"]==2
        if use_pysat:
            if s:
                f=WCNF()
                for c in h: f.append(c)
                for w,c in s: f.append(c,weight=w)
                with RC2(f,solver="g3") as rc2:
                    model=rc2.compute(); assert model is not None
                    assert rc2.cost==truth["optimum"],row["id"]
                    assert assignment_cost(model,h,s)==truth["optimum"]
                stats["rc2_glucose3_optimum_checks"]+=1
            else:
                with Solver(name="m22",bootstrap_with=h) as solver:
                    sat=solver.solve(); assert sat==(truth["status"]=="SAT"),row["id"]
                    if sat:
                        m=solver.get_model(); bb=[]
                        for lit in m:
                            if abs(lit)<=n and not solver.solve(assumptions=[-lit]): bb.append(lit)
                        assert sorted(bb,key=abs)==truth["backbone"],row["id"]
                stats["minisat22_sat_and_backbone_checks"]+=1
        groups.setdefault(row["group_id"],[]).append(row)
        if row["variant"]=="challenge": parsed[row["group_id"]]=(n,h,s)
        if row["variant"]=="disguised":
            cn,ch,cs=parsed.pop(row["group_id"]); assert cn==n
            mapping={int(k):v for k,v in row["challenge_to_disguised_literal_map"].items()}
            assert set(mapping)==set(range(1,n+1)) and {abs(v) for v in mapping.values()}==set(range(1,n+1))
            def mapped(c): return [mapping[abs(l)]*(1 if l>0 else -1) for l in c]
            assert canonical([mapped(c) for c in ch],[(w,mapped(c)) for w,c in cs])==canonical(h,s)
            challenge_truth=groups[row["group_id"]][1]["truth"]
            for k in ("status","model_count","optimum","optimal_model_count"):
                assert challenge_truth.get(k)==truth.get(k)
            if truth["backbone"] is not None: assert sorted(mapped(challenge_truth["backbone"]),key=abs)==truth["backbone"]
            stats["exact_bijection_checks"]+=1
        stats["exhaustive_truth_table_checks"]+=1; family_stats[sid]+=1
        if (pos+1)%360==0: print(f"Verified {pos+1}/{len(rows)}",flush=True)
    assert not parsed
    assert scalar_scenarios=={spec["id"] for spec in scenarios}
    for gid,members in groups.items():
        assert {r["variant"] for r in members}=={"control","challenge","disguised"}
        assert len({r["split"] for r in members})==1
    for spec in scenarios:
        assert family_stats[spec["id"]]==spec["examples"]
        assert sum(g[0]["scenario_id"]==spec["id"] for g in groups.values())>=100
    pair_rows=[json.loads(l) for l in (root/"pairs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(pair_rows)==len(groups)
    for pair in pair_rows:
        members=groups[pair["group_id"]]; a,b,_=members
        assert pair["paths"]==[r["path"] for r in members]
        for key in ("status","model_count","optimum"):
            assert pair.get("control_"+key)==a["truth"].get(key)
            assert pair.get("challenge_"+key)==b["truth"].get(key)
    summary=json.loads((root/"summary.json").read_text(encoding="utf-8"))
    assert summary["instances"]==len(rows) and summary["groups"]==len(groups)
    assert summary["distinct_formulas_ignoring_clause_and_literal_order"]==len(formulas)
    report=dict(status="PASS",instances=len(rows),groups=len(groups),scenarios=len(scenarios),
        checks=dict(stats),all_inputs_well_formed=True,all_files_distinct_ignoring_clause_literal_order=True,
        exhaustive_nvars_limit=18,pysat_enabled=use_pysat,pysat_version=pysat.__version__ if use_pysat else None,
        manifest_sha256=hashlib.sha256((root/"manifest.jsonl").read_bytes()).hexdigest(),
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ("generate.py","verify.py")},
        elapsed_seconds=round(time.time()-started,3),baseline_methods_run=0,
        limitations="Bounded compact formulas; no claim of baseline failure or publication-scale hardness. Truth-table labels are computational certificates, not DRAT/LRAT/VeriPB proof files.")
    dump(root/"validation.json",report); print(json.dumps(report,indent=2))


if __name__=="__main__":
    # The original v2 implementation is preserved in releases/v2/verify.py.
    import runpy
    sys.path.insert(0,str(ROOT/'tools'))
    runpy.run_path(str(ROOT/'tools'/'verify_all.py'),run_name='__main__')
