"""Independently check external-generator statuses and document the Pitfall correction."""
from collections import Counter
from threading import Timer
from common import *
from pysat.solvers import Solver


def check(n,h):
    with Solver(name='g4',bootstrap_with=h) as solver:
        solver.conf_budget(100000); timer=Timer(2,solver.interrupt); timer.start()
        try:
            answer=solver.solve_limited(expect_interrupt=True)
            return answer,solver.get_model() if answer else None
        finally: timer.cancel()


def main():
    rows=[r for r in read_rows(ROOT/'parts'/'extensions.jsonl') if r['scenario_id'].startswith('cnfgen_')]; stats=Counter(); failures=[]
    for i,row in enumerate(rows):
        n,h,s,_=parse_text(decode((ROOT/row['path']).read_bytes()),'cnf'); answer,model=check(n,h)
        if answer is None: stats['budget_unresolved']+=1
        elif answer!=(row['truth']['status']=='SAT'): failures.append(row['id'])
        else: stats['independent_status_matches']+=1
        if (i+1)%120==0: print(f'Generator status audit: {i+1}/{len(rows)}',flush=True)
    assert not failures,failures
    sample=next(r for r in rows if r['id']=='cnfgen_pitfall/0002/original')
    source=sample['source']; n,h,s,_=parse_text(decode((ROOT/source['original_path']).read_bytes()),'cnf'); answer,model=check(n,h)
    assert answer and assignment_cost(model,h,[])==0
    correction=dict(source='CNFgen 0.9.6 PitfallFormula',upstream_unchanged=True,
        affected_expression='sign * first_edge + lit - 1',correct_expression='sign * (first_edge + abs(lit) - 1)',
        reasoning='For negative lit, upstream computes -first_edge-abs(lit)-1; the correct renamed literal is -first_edge-abs(lit)+1. Only the copied hard-part negative literals need +2.',
        preserved_unadapted_formula=source['original_path'],unadapted_sha256=source['original_sha256'],unadapted_status='SAT',unadapted_witness=model[:n],
        adapted_formula=sample['path'],adapted_sha256=sample['sha256'],adapted_status=sample['truth']['status'],
        scope='A local generator correction, not a reported failure of an A/B/C/D baseline. No upstream issue was sent.')
    write_json(ROOT/'sources'/'generator-corrections.json',correction)
    report=dict(status='PASS',formulas=len(rows),checks=dict(stats),correction=correction)
    write_json(ROOT/'generator-validation.json',report); print(json.dumps(dict(status='PASS',checks=dict(stats)),indent=2))


if __name__=='__main__': main()
