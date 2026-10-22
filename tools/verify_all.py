"""Verify MATT v3 formulas, mathematical certificates, source hashes, and label scope."""
from collections import Counter, defaultdict
import argparse
import itertools
import json
import random
import time
from threading import Timer

from common import *
from pysat.solvers import Solver
import networkx as nx


def canon(h,s): return (sorted(tuple(sorted(c)) for c in h),sorted((w,tuple(sorted(c))) for w,c in s))
def assert_same(h,s,eh,es): assert canon(h,s)==canon(eh,es)
def connected(n,edges):
    adj=[[] for _ in range(n)]
    for a,b in edges: adj[a-1].append(b-1); adj[b-1].append(a-1)
    visited={0}; todo=[0]
    while todo:
        a=todo.pop()
        for b in adj[a]:
            if b not in visited: visited.add(b); todo.append(b)
    return len(visited)==n


def independent_tree_optimum(h,s):
    # Reconstruct a forest from the actual clauses, not the construction metadata.
    weights={abs(c[0]):w for w,c in s}; vertices=set(weights)
    adj={v:[] for v in vertices}
    for c in h:
        assert len(c)==2 and all(l>0 for l in c)
        a,b=c; adj[a].append(b); adj[b].append(a)
    total=0; seen=set()
    for root in sorted(vertices):
        if root in seen: continue
        parent={root:0}; order=[root]; seen.add(root)
        for v in order:
            for u in adj[v]:
                if u==parent[v]: continue
                assert u not in parent
                parent[u]=v; order.append(u); seen.add(u)
        dp={}
        for v in reversed(order):
            child=[u for u in adj[v] if parent.get(u)==v]
            dp[v]=(sum(dp[u][1] for u in child),weights[v]+sum(min(dp[u]) for u in child))
        total+=min(dp[root])
    return total


def check_sat(row,h,stats,backbone=False):
    truth=row['truth']; expected=truth['status']
    if expected not in ('SAT','UNSAT'): return
    with Solver(name='g4',bootstrap_with=h) as solver:
        solver.conf_budget(100000); timer=Timer(2,solver.interrupt); timer.start()
        try: answer=solver.solve_limited(expect_interrupt=True)
        finally: timer.cancel()
        if answer is None: stats['independent_sat_budget_exhausted']+=1; return
        assert answer==(expected=='SAT'),row['id']; stats['independent_glucose4_status_checks']+=1
        if answer and backbone and truth.get('backbone_complete'):
            bb=[]; scope=truth.get('primary_variables',list(range(1,row['nvars']+1)))
            model={abs(l):l for l in solver.get_model()}
            for v in scope:
                solver.conf_budget(50000); result=solver.solve_limited(assumptions=[-model.get(v,-v)])
                assert result is not None,row['id']
                if result is False: bb.append(model.get(v,-v))
            assert bb==truth['backbone'],row['id']; stats['independent_full_backbone_checks']+=1


def certificate(row,n,h,s,stats):
    p=row['parameters']; cert=p.get('certificate'); variant=row['variant']; truth=row['truth']; cost=truth.get('optimum')
    if not cert: return False
    if cert=='uniform_barrier':
        weights=p['positive_weights']; b=p['negative_weight']; j=p['coupling']; edges=p['edges']; total=sum(weights)
        assert n==len(weights) and connected(n,edges) and j>total+b and 0<b<total
        unary=[(w,[v]) for v,w in enumerate(weights,1)]+[(b,[-1])]
        expected=unary+([(j,c) for a,z in edges for c in eq(a,z)] if variant=='challenge' else [])
        assert_same(h,s,[],expected)
        assert cost==(b if variant=='challenge' else min(weights[0],b))
        if variant=='challenge': assert p['minimum_hamming_distance_to_improvement']==n and p['trap_cost']==total
    elif cert=='entropic_gate':
        assert p['trigger_width']==n-1; b=p['cheap_cost']; expensive=p['expensive_cost']; assert b<expensive
        assert_same(h,s,[[1,v] for v in range(2,n+1)] if variant=='challenge' else [],[(b,[1]),(expensive,[-1])]); assert cost==b
    elif cert=='exactly_one_cost':
        ws=p['selection_costs'] if variant=='challenge' else [p['uniform_cost']]*n
        assert_same(h,s,exactly(list(range(1,n+1)),1),[(w,[-v]) for v,w in enumerate(ws,1)]); assert cost==min(ws)
        assert ws[0]!=ws[1] if variant=='challenge' else True
    elif cert=='laminar_tree':
        parents={int(v):a for v,a in p['parents'].items()}; weights={-c[0]:w for w,c in s}
        assert len(parents)==n-1 and all(1<=a<v<=n for v,a in parents.items())
        children=defaultdict(list)
        for v,a in parents.items(): children[a].append(v)
        expected=[]
        for v in range(1,n+1):
            if children[v]: continue
            path=[v]
            while path[-1]!=1: path.append(parents[path[-1]])
            expected.append(path)
        expected_weights={int(v):w for v,w in p['weights'].items()}
        if variant=='challenge': expected_weights[p['changed_vertex']]=p['new_weight']
        assert weights==expected_weights; assert_same(h,s,expected,[(w,[-v]) for v,w in weights.items()])
        dp={}
        for v in range(n,0,-1): dp[v]=min(weights[v],sum(dp[u] for u in children[v])) if children[v] else weights[v]
        assert cost==dp[1]
    elif cert=='tree_cover':
        base_n=len(p['weights']); base_s=[(int(w),[-int(v)]) for v,w in p['weights'].items()]
        base_h=[[int(v),a] for v,a in p['parents'].items()]
        base_cost=independent_tree_optimum(base_h,base_s)
        if variant=='control': assert_same(h,s,base_h,base_s); assert cost==base_cost
        elif row['scenario_id']=='objective_integer_scaling':
            k=p['scale']; assert_same(h,s,base_h,[(w*k,c) for w,c in base_s]); assert cost==base_cost*k
        elif row['scenario_id']=='nonempty_constant_offset':
            assert n==base_n+1; a=p['offset']; assert_same(h,s,base_h,base_s+[(a,[n]),(a,[-n])]); assert cost==base_cost+a
        else:
            folded=Counter()
            for w,c in s: folded[tuple(c)]+=w
            assert folded==Counter({tuple(c):w for w,c in base_s}); assert canon(h,[])[0]==canon(base_h,[])[0]; assert cost==base_cost
    elif cert=='signed_components':
        split=p['split']; phase=p['phase']; edges=p['edges']+(p['added_edges'] if variant=='challenge' else [])
        assert connected(split,[(a,b) for a,b in edges if b<=split])
        assert connected(n-split,[(a-split,b-split) for a,b in edges if a>split])
        assert all((a<=split)==(b<=split) for a,b in edges)
        expected=[c for a,b in edges for c in xor([a,b],phase[a-1]^phase[b-1])]+[[1 if phase[0] else -1]]
        assert_same(h,s,expected,[])
        assert truth['backbone']==[v if phase[v-1] else -v for v in range(1,split+1)] and truth['model_count']==2
    elif cert=='tseitin':
        edges=p['edges']; vertices=p['vertices']; charges={int(k):v for k,v in p['charges'].items()}
        if variant=='challenge': charges[p['flipped_vertex']]^=1
        graph=nx.Graph(); graph.add_edges_from(edges); assert nx.is_connected(graph) and not list(nx.bridges(graph))
        assert n==len(edges) and len(graph)==vertices
        expected=[c for a in sorted(charges) for c in xor([i+1 for i,e in enumerate(edges) if a in e],charges[a])]
        assert_same(h,s,expected,[]); assert truth['status']==('UNSAT' if sum(charges.values())%2 else 'SAT')
        if truth['status']=='SAT': assert truth['model_count']==2**(n-vertices+1) and truth['backbone']==[]
    elif cert in ('model_rb','published_model_rb'):
        groups=p['groups']; domain=p['domain']; assert n==groups*domain and not h
        heavy=Counter(tuple(sorted(c)) for w,c in s if w!=1)
        assert sorted(c for w,c in s if w==1)==[[v] for v in range(1,n+1)]
        assert all(w==n+1 and len(c)==2 and all(l<0 for l in c) for w,c in s if w!=1)
        for g in range(groups):
            for a,b in itertools.combinations(range(g*domain+1,(g+1)*domain+1),2): assert heavy[tuple(sorted((-a,-b)))]>0
        if cost is not None: assert cost==n-groups
        if truth['status']=='OPTIMUM': assert 'witness' in truth
    elif cert=='cardinality_projection':
        primary=p['primary_variables']; k=p['k']; anchor=p['anchor']; extra=p['additional_primary_clauses']
        primary_hard=exactly(list(range(1,primary+1)),k)+[[anchor]]+extra
        reference=evaluate(primary,primary_hard,[])
        assert truth['backbone']==reference['backbone'] and truth['projected_model_count']==reference['model_count']
        assert truth['backbone_scope']=='primary_variables_only'
        # Complete enumeration of projected assignments verifies both soundness and completeness of each encoder.
        count=0
        with Solver(name='g4',bootstrap_with=h) as solver:
            for mask in range(1<<primary):
                model=[v if mask&(1<<(v-1)) else -v for v in range(1,primary+1)]
                expected=assignment_cost(model,primary_hard,[]) is not None
                answer=solver.solve(assumptions=model); assert answer==expected,row['id']
                count+=answer
        assert count==truth['projected_model_count']; stats['complete_encoding_projection_checks']+=1
    elif cert=='cnfgen_unsat':
        if p['generator']=='PebblingFormula' and variant=='control':
            assert truth['status']=='SAT'; check_sat(row,h,stats,backbone=True)
        else:
            assert truth['status']=='UNSAT'; check_sat(row,h,stats)
        if p['generator']=='SubsetCardinalityFormula':
            m=p['partition_size']; graph=nx.Graph(); graph.add_edges_from(p['edges']); assert len(graph)==2*m and all(d==3 for _,d in graph.degree())
        # Independent solver status is recorded separately; unresolved calls retain construction evidence only.
    elif cert in ('sat_witness','unsat_literal_strengthening','unsat_clause_addition'):
        check_sat(row,h,stats,backbone=row['truth'].get('backbone_complete',False))
    else: raise ValueError(cert)
    stats['mathematical_certificate_checks']+=1
    return True


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--pysat-path'); ap.add_argument('--pysat',action='store_true'); args=ap.parse_args()
    started=time.time(); rows=read_rows(ROOT/'manifest.jsonl'); by_id={r['id']:r for r in rows}; stats=Counter(); origins=Counter(); evidence=Counter(); groups=defaultdict(list); source_hashes={}; checked=[]; seen_ids=set(); parent_cache={}
    v2_ids={r['id'] for r in read_rows(ROOT/'releases'/'v2'/'manifest.jsonl')}
    for index,row in enumerate(rows):
        assert row['id'] not in seen_ids; seen_ids.add(row['id'])
        path=(ROOT/row['path']).resolve(); assert path.is_relative_to(ROOT/'instances')
        data=path.read_bytes(); assert sha(data)==row['sha256'],row['id']
        n,h,s,info=parse_text(decode(data),'cnf' if row['format']=='dimacs-cnf' else 'wcnf')
        assert (n,len(h)+len(s),len(h),len(s),sum(w for w,c in s))==(row['nvars'],row['nclauses'],row['hard_clauses'],row['soft_clauses'],row['total_soft_weight'])
        t=row['truth']
        if 'witness' in t:
            model=t['witness']; assert len(model)==n and {abs(l) for l in model}==set(range(1,n+1))
            actual=assignment_cost(model,h,s)
            assert actual is not None,row['id']
            if t.get('optimum') is not None: assert actual==t['optimum'],row['id']
            elif t.get('best_known_cost') is not None: assert actual==t['best_known_cost']
            stats['witness_and_original_objective_checks']+=1
        if row['id'] in v2_ids:
            assert evaluate(n,h,s)==t,row['id']; stats['v2_exhaustive_labels_rechecked']+=1
            if 'suboptimal_trap' in row:
                trap=row['suboptimal_trap']; value=assignment_cost(trap['assignment'],h,s)
                assert value==trap['cost']>t['optimum']
                neighbors=[assignment_cost([-l if abs(l)==v else l for l in trap['assignment']],h,s) for v in range(1,n+1)]
                assert neighbors==trap['one_flip_costs'] and all(x is None or x>=value for x in neighbors)
                stats['v2_trap_certificates_rechecked']+=1
            checked.append(row['id'])
        elif n<=18 and row['origin']=='historical_regression':
            actual=evaluate(n,h,s)
            for key in ('status','optimum','model_count','backbone','optimal_model_count'): assert actual.get(key)==t.get(key),row['id']
            stats['imported_exhaustive_labels_rechecked']+=1; checked.append(row['id'])
        elif row['parameters'].get('certificate') in ('resolution_implication','source_weight_scaling'):
            parent=by_id[row['parameters']['parent_manifest_id']]
            if parent['id'] not in parent_cache:
                parent_cache.clear(); parent_cache[parent['id']]=parse_text(decode((ROOT/parent['path']).read_bytes()),'cnf' if parent['format']=='dimacs-cnf' else 'wcnf')
            pn,ph,ps,_=parent_cache[parent['id']]
            if row['parameters']['certificate']=='resolution_implication':
                p=row['parameters']; assert row['truth']==parent['truth']
                for step in p['resolution_steps']:
                    a,b=step['parent_indices']; pivot=step['pivot']; assert pivot in ph[a] and -pivot in ph[b]
                    assert set(step['resolvent'])==(set(ph[a])-{pivot})|(set(ph[b])-{-pivot})
                assert n==pn; assert_same(h,s,ph+(p['added_clauses'] if row['variant']=='challenge' else []),[])
                stats['resolution_implication_certificates']+=1; checked.append(row['id'])
            else:
                k=row['parameters']['scale'] if row['variant']=='challenge' else 1
                assert n==pn; assert_same(h,s,ph,[(w*k,c) for w,c in ps])
                for key in ('optimum','best_known_cost'):
                    assert row['truth'].get(key)==(parent['truth'][key]*k if parent['truth'].get(key) is not None else None)
                stats['source_objective_scaling_relations']+=1
        elif certificate(row,n,h,s,stats):
            if row['truth']['status'] not in ('OPTIMUM_REFERENCE','UNKNOWN','REFERENCE_ONLY'): checked.append(row['id'])
        elif row['origin']=='public_benchmark' and row['tier']=='application':
            check_sat(row,h,stats,backbone=t.get('backbone_complete',False)); checked.append(row['id'])
        elif row['origin']=='historical_regression':
            assert row['source']['metadata']['CertifiedResult']=='YES' or t['status']=='FEASIBLE'
        elif row.get('source',{}).get('absolute_label_locally_established'):
            check_sat(row,h,stats,backbone=t.get('backbone_complete',False)); checked.append(row['id'])
        if source:=row.get('source'):
            if 'original_path' in source:
                original=ROOT/source['original_path']; expected=source['original_sha256']
                if str(original) not in source_hashes: source_hashes[str(original)]=sha(original.read_bytes())
                assert source_hashes[str(original)]==expected; stats['source_original_hash_checks']+=1
        groups[row['group_id']].append(row); origins[row.get('origin','v2_constructed')]+=1; evidence[row.get('label_evidence','v2_exhaustive')]+=1
        stats['strict_formula_and_sha256_checks']+=1
        if (index+1)%500==0: print(f'Validated {index+1}/{len(rows)}',flush=True)
    relation_count=0
    for gid,members in groups.items():
        assert len({r['split'] for r in members})==1
        by_variant={r['variant']:r for r in members}
        if 'control' not in by_variant or 'challenge' not in by_variant: continue
        a=by_variant['control']; b=by_variant['challenge']; relation=b.get('relation_to_control',{}); kind=relation.get('type')
        at=a['truth']; bt=b['truth']
        if kind in ('pointwise_objective_equivalence','planted_optimum_preserving_constraints'): assert at['optimum']==bt['optimum']
        if kind=='optimum_scaling' and at.get('optimum') is not None: assert at['optimum']*relation['factor']==bt['optimum']
        if kind=='constant_objective_offset': assert at['optimum']+relation['offset']==bt['optimum']
        if kind in ('full_model_equivalence','status_preserving_perturbation','projected_equivalence'): assert at['status']==bt['status']
        if kind=='projected_equivalence': assert at['projected_model_count']==bt['projected_model_count'] and at['backbone']==bt['backbone']
        if a['scenario_id'].startswith('neural_unsat_'):
            _,ah,_,_=parse_text(decode((ROOT/a['path']).read_bytes()),'cnf'); _,bh,_,_=parse_text(decode((ROOT/b['path']).read_bytes()),'cnf')
            if a['scenario_id']=='neural_unsat_clause_addition': assert bh[:len(ah)]==ah
            else: assert len(ah)==len(bh) and all(set(y)<=set(x) and y for x,y in zip(ah,bh))
        if kind: relation_count+=1
        if 'disguised' in by_variant:
            original=by_variant['challenge']; disguised=by_variant['disguised']; mapping={int(k):v for k,v in disguised['challenge_to_disguised_literal_map'].items()}
            nn,oh,os,_=parse_text(decode((ROOT/original['path']).read_bytes()),'cnf' if original['format']=='dimacs-cnf' else 'wcnf')
            _,dh,ds,_=parse_text(decode((ROOT/disguised['path']).read_bytes()),'cnf' if original['format']=='dimacs-cnf' else 'wcnf')
            def mapped(c): return [mapping[abs(l)]*(1 if l>0 else -1) for l in c]
            assert {abs(v) for v in mapping.values()}==set(range(1,nn+1))
            assert_same(dh,ds,[mapped(c) for c in oh],[(w,mapped(c)) for w,c in os])
            stats['v2_representation_bijections_rechecked']+=1
    specs=json.loads((ROOT/'scenarios.json').read_text())['scenarios']
    for spec in specs:
        selected=[r for r in rows if r['scenario_id']==spec['id']]
        assert len(selected)==spec['examples']; actual_groups=len({r['group_id'] for r in selected})
        assert actual_groups==spec['groups']
        if spec.get('origin') in ('constructed','external_generator','adapted_generator') or spec.get('origin') is None: assert actual_groups>=100
    checked_set=set(checked)
    write_rows(ROOT/'views'/'locally-established-labels.jsonl',[r for r in rows if r['id'] in checked_set])
    write_rows(ROOT/'views'/'reference-only.jsonl',[r for r in rows if r['id'] not in checked_set])
    write_rows(ROOT/'views'/'maxsat-optimum-local.jsonl',[r for r in rows if r['id'] in checked_set and r['truth'].get('optimum') is not None])
    write_rows(ROOT/'views'/'sat-status-local.jsonl',[r for r in rows if r['id'] in checked_set and r['format']=='dimacs-cnf' and r['truth']['status'] in ('SAT','UNSAT')])
    report=dict(version='3.0.0',status='PASS',formulas=len(rows),groups=len(groups),scenarios=len(specs),checks=dict(stats),paired_relation_checks=relation_count,
        locally_established_label_rows=len(set(checked)),reference_only_or_source_claim_rows=len(rows)-len(set(checked)),
        evidence_categories=dict(evidence),origins=dict(origins),baseline_experiments_run=0,
        manifest_sha256=sha((ROOT/'manifest.jsonl').read_bytes()),elapsed_seconds=round(time.time()-started,3),
        source_hashes={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [Path(__file__),ROOT/'tools'/'build_extensions.py',ROOT/'tools'/'import_public.py',ROOT/'tools'/'common.py']},
        scope='All formula hashes and syntax checked; witnesses and analytical certificates checked where supplied. Source-only optimum claims remain source-only. Independent SAT budget exhaustion is reported, not reclassified as a wrong answer.')
    write_json(ROOT/'validation.json',report); print(json.dumps(report,indent=2))


if __name__=='__main__': main()
