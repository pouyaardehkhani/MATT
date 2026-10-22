"""Build MATT v3 mathematical families. Does not run research baselines."""
from collections import Counter
import importlib.metadata
import itertools
import json
import math
import random
import shutil
from pathlib import Path
import sys

from common import *
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
import networkx as nx
from cnfgen.families.pitfall import PitfallFormula
from cnfgen.families.pebbling import PebblingFormula, StoneFormula
from cnfgen.families.subsetcardinality import SubsetCardinalityFormula

COUNT=120
SPECS=[
 scenario('scaled_collective_barrier','wcnf','Collective barriers from 50 to 5000 variables','A connected weighted equality network has two uniform basins with different costs.','Every nonuniform assignment pays a coupling larger than the entire unary objective. The only assignment better than the supplied trap differs in every core bit.','Replace uncoupled preferences by strong connected couplings.',tier='scaled'),
 scenario('entropic_selector_basin','wcnf','A rare optimum competes with exponentially many near optima','A gate permits all trigger bits freely in the expensive branch but requires all of them in the cheap branch.','The objective minimum is unchanged while the proportion of optimal feasible assignments becomes 1/(2^k+1).','Add the multi-bit feasibility trigger.',tier='scaled'),
 scenario('objective_asymmetric_symmetry','wcnf','Feasibility symmetry is not objective symmetry','Exactly one option is selected from interchangeable hard-feasible choices.','Unequal selection costs destroy objective symmetries despite preserving every hard-feasible exchange.','Change uniform selection costs to distinct costs.'),
 scenario('laminar_shared_repairs','wcnf','Nested repair demands share an ancestor choice','Each leaf demand may be repaired by selecting any ancestor on its root-to-leaf path.','A single ancestor repairs many nested demands; independent per-demand cost addition can be invalid.','Change the cost of an internal shared repair.',tier='scaled'),
 scenario('cardinality_projection_encoding','cnf','Different auxiliary encodings of the same choices','An exactly-k selection constraint is encoded with sequential counters and a totalizer.','Answers must agree after projection to primary variables; auxiliary backbones and extension multiplicities need not agree.','Replace the complete auxiliary encoding; retain primary constraints and variable map.'),
 scenario('implied_constraint_amplification','cnf','Implied constraints reshape a correlated formula','Two signed connected components contain one anchored orientation and one free orientation.','Adding implied equalities changes occurrence counts and syntactic graph structure without changing any model.','Add many transitive signed equalities.',tier='scaled'),
 scenario('soft_weight_partition','wcnf','Partitioning a clause weight preserves every assignment cost','A weighted tree-cover objective is represented with one clause per preference.','Replacing a weight by positive summands must preserve the objective pointwise.','Split each positive weight into smaller copies.'),
 scenario('objective_integer_scaling','wcnf','Exact integer objective scaling','A weighted tree-cover instance has an optimum calculated by dynamic programming.','Multiplying every soft weight by k must multiply its optimum by k and preserve optimal assignments.','Scale every soft weight by a positive integer.'),
 scenario('nonempty_constant_offset','wcnf','A provable constant objective offset','A tree-cover problem gains a fresh soft contradictory pair with equal weights.','Exactly one member of the nonempty fresh-variable pair is false, adding a constant for every feasible assignment.','Add (z,a) and (NOT z,a) on a fresh variable.'),
 scenario('general_graph_tseitin','cnf','Matched local statistics, different global parity','Edge variables satisfy parity charges on a connected bridgeless regular graph.','Flipping one vertex charge changes consistency while preserving the factor graph, clause widths, and literal counts per local parity constraint.','Flip one vertex charge, keeping all other data fixed.'),
 scenario('cnfgen_pitfall','cnf','Pitfall formulas with checked signed edge mapping','Pitfall formulas contain easy and hard parts plus a gadget directing common heuristics to the hard part.','A structured heuristic-deception family broadens MATT beyond small planted motifs. The adapter corrects an upstream signed-offset error, documented with preserved originals.','Independent seeds and graph/gadget parameters.',origin='adapted_generator'),
 scenario('cnfgen_pebbling','cnf','Propagation across reconvergent directed graphs','A unique-sink DAG propagates source truth toward a forbidden sink.','Many paths share consequences; the sink contradiction is global in the graph construction.','Add the original generator\'s sink-false clause.',origin='external_generator'),
 scenario('cnfgen_stone','cnf','Stone-color propagation conflicts','Stones on graph sources are red and inherit redness, while sink stones must be blue.','The interaction of stone assignments and propagation adds a distinct structured obstruction.','Vary the DAG, number of stones, and associated assignments.',origin='external_generator'),
 scenario('cnfgen_subset_cardinality','cnf','Locally feasible cardinalities, globally impossible totals','A 3-regular bipartite incidence graph requires at least two incident selected edges at each left vertex and at most one at each right vertex.','Summing the left requirements exceeds the right capacity although each local constraint is satisfiable.','Vary the bipartite graph while retaining the inconsistent total.',origin='external_generator'),
 scenario('model_rb_hidden_optimum','wcnf','Generated Model RB hidden-optimum cores','One planted choice per variable group avoids all forbidden pairs.','Heavy pair penalties make every optimum respect at-most-one choices; the supplied planted assignment attains the lower bound.','Add cross-group forbidden pairs that keep the planted optimum.',tier='scaled',origin='adapted_generator'),
 scenario('neural_sat_witness_perturbation','cnf','Witness-preserving SAT perturbations','Random clauses are added until the next clause first destroys satisfiability; the satisfiable prefix is retained.','Additional clauses satisfied by a known witness retain SAT while altering structural features.','Add witness-compatible clauses.',origin='adapted_generator'),
 scenario('neural_unsat_literal_deletion','cnf','UNSAT survives strengthening by literal deletion','A first-conflict random formula is UNSAT.','Deleting literals from nonunit clauses strengthens the formula and therefore preserves UNSAT.','Delete selected literals without creating empty clauses.',origin='adapted_generator'),
 scenario('neural_unsat_clause_addition','cnf','UNSAT survives added constraints','A first-conflict random formula is UNSAT.','Adding well-formed nonempty clauses preserves the UNSAT label while changing local statistics.','Add extra random nonempty clauses.',origin='adapted_generator'),
]


def rng_for(sid,i): return random.Random(int(sha(f'20261016/v3/{sid}/{i}'.encode())[:16],16))
def cost_truth(n,h,s,cost,model,**extra):
    assert assignment_cost(model,h,s)==cost
    return dict(status='OPTIMUM',optimum=cost,witness=model,backbone=None,backbone_complete=False,
                label_evidence='construction_proved; locally checked witness and certificate',**extra)
def all_model(n,positive=True): return [v if positive else -v for v in range(1,n+1)]
def edges_connected(rng,n):
    edges={(rng.randrange(1,v),v) for v in range(2,n+1)}
    for _ in range(n//3):
        a,b=sorted(rng.sample(range(1,n+1),2)); edges.add((a,b))
    return sorted(edges)
def tree_case(rng,n):
    parents={v:rng.randrange(1,v) for v in range(2,n+1)}
    weights={v:rng.randint(2,35) for v in range(1,n+1)}
    h=[[p,v] for v,p in parents.items()]; s=[(weights[v],[-v]) for v in range(1,n+1)]
    return parents,weights,h,s
def cover_dp(parents,weights,n):
    children={v:[] for v in range(1,n+1)}
    for v,p in parents.items(): children[p].append(v)
    yes={}; no={}
    for v in range(n,0,-1):
        yes[v]=weights[v]+sum(min(yes[c],no[c]) for c in children[v])
        no[v]=sum(yes[c] for c in children[v])
    selected=set()
    def walk(v,parent_selected):
        chosen=not parent_selected or yes[v]<=no[v]
        if chosen: selected.add(v)
        for c in children[v]: walk(c,chosen)
    walk(1,True)
    return min(yes[1],no[1]),[v if v in selected else -v for v in range(1,n+1)]
def laminar_dp(parents,weights,n):
    children={v:[] for v in range(1,n+1)}
    for v,p in parents.items(): children[p].append(v)
    value={}; select={}
    for v in range(n,0,-1):
        below=sum(value[c] for c in children[v]) if children[v] else math.inf
        select[v]=weights[v]<=below; value[v]=min(weights[v],below)
    chosen=set()
    def walk(v):
        if select[v]: chosen.add(v)
        else:
            for c in children[v]: walk(c)
    walk(1)
    return int(value[1]),[v if v in chosen else -v for v in range(1,n+1)]


def archive_v2():
    dest=ROOT/'releases'/'v2'; dest.mkdir(parents=True,exist_ok=True)
    for name in ('manifest.jsonl','pairs.jsonl','scenarios.json','scenarios.md','summary.json','validation.json','reproducibility.json','README.md','generate.py','verify.py'):
        path=dest/name
        if not path.exists(): shutil.copy2(ROOT/name,path)


def neural_pair(rng,n):
    clauses=[]
    with Solver(name='m22') as solver:
        for _ in range(n*15):
            width=min(n,2+sum(rng.random()>.4 for _ in range(3)))
            clause=[rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),width)]
            solver.add_clause(clause)
            if not solver.solve(): return clauses,clauses+[clause]
            clauses.append(clause)
    raise RuntimeError('Random prefix failed to reach UNSAT')


def build(resume=False,only=None):
    archive_v2(); rows=read_rows(ROOT/'parts'/'extensions.jsonl') if resume and (ROOT/'parts'/'extensions.jsonl').exists() else []
    catalogue=json.loads((ROOT/'parts'/'extension-scenarios.json').read_text()) if rows else []
    if only:
        rows=[r for r in rows if r['scenario_id'] not in only]
        catalogue=[s for s in catalogue if s['id'] not in only]
    completed={s['id'] for s in catalogue}
    generator_source=dict(url='https://github.com/MassimoLauria/cnfgen',version=importlib.metadata.version('CNFgen'),
        snapshot='sources/archives/cnfgen-source.zip',actual_generator='installed CNFgen '+importlib.metadata.version('CNFgen'))
    neural_source=dict(url='https://github.com/johannaSommer/generalization-neural-co-solvers',snapshot='sources/archives/neural-robustness-source.zip',
        adaptation='standard-library/PySAT implementation of generation and label-preserving operations; no neural model attack claimed')
    for spec in SPECS:
        if only and spec['id'] not in only: continue
        if spec['id'] in completed: continue
        sid=spec['id']; before=len(rows); fingerprints=set()
        for i in range(COUNT):
            rng=rng_for(sid,i); source=None; outputs=[]; params={}; n=0
            if sid=='scaled_collective_barrier':
                n=(50,200,1000,5000)[i%4]+rng.randrange(0,10) if i%4!=3 else 5000-rng.randrange(0,10)
                weights=[rng.randint(2,9) for _ in range(n)]; p=sum(weights); b=rng.randint(p//3,p*2//3); j=p+b+1; edges=edges_connected(rng,n)
                s=[(w,[v]) for v,w in enumerate(weights,1)]+[(b,[-1])]; cs=s+[(j,c) for a,z in edges for c in eq(a,z)]
                model=all_model(n); model[0]=-1 if weights[0]<b else 1
                a=cost_truth(n,[],s,min(weights[0],b),model); btruth=cost_truth(n,[],cs,b,all_model(n))
                params=dict(certificate='uniform_barrier',positive_weights=weights,negative_weight=b,coupling=j,edges=edges,
                            trap_cost=p,trap_core_assignment='all_false',minimum_hamming_distance_to_improvement=n)
                outputs=[('control',n,[],s,a,None),('challenge',n,[],cs,btruth,dict(type='semantic_coupling'))]
            elif sid=='entropic_selector_basin':
                k=(50,200,1000,5000)[i%4]+rng.randint(0,5); n=k+1; b=rng.randint(2,15); p=b+rng.randint(1,20)
                s=[(b,[1]),(p,[-1])]; h=[[1,v] for v in range(2,n+1)]
                model=[-1]+list(range(2,n+1)); truth=cost_truth(n,h,s,b,model)
                params=dict(certificate='entropic_gate',trigger_width=k,cheap_cost=b,expensive_cost=p,
                    challenge_optimal_model_count='1',challenge_suboptimal_model_count=f'2^{k}',control_optimal_model_count=f'2^{k}')
                outputs=[('control',n,[],s,truth,None),('challenge',n,h,s,truth,dict(type='semantic_feasibility_trigger',optimum_relation='unchanged'))]
            elif sid=='objective_asymmetric_symmetry':
                n=rng.randint(5,30); h=exactly(list(range(1,n+1)),1); w=rng.randint(2,20)
                s=[(w,[-v]) for v in range(1,n+1)]; weights=rng.sample(range(1,4*n+1),n); cs=[(a,[-v]) for v,a in enumerate(weights,1)]
                model=all_model(n,False); model[0]=1
                cm=all_model(n,False); best=weights.index(min(weights)); cm[best]=best+1
                a=cost_truth(n,h,s,w,model,backbone_scope='all_hard_feasible_variables'); b=cost_truth(n,h,cs,min(weights),cm)
                params=dict(certificate='exactly_one_cost',selection_costs=weights,uniform_cost=w,
                    non_objective_symmetry=[1,2],exchange_costs=[weights[0],weights[1]])
                outputs=[('control',n,h,s,a,None),('challenge',n,h,cs,b,dict(type='semantic_weight_change'))]
            elif sid=='laminar_shared_repairs':
                n=rng.randint(30,250); parents={v:rng.randrange(1,v) for v in range(2,n+1)}; weights={v:rng.randint(2,40) for v in range(1,n+1)}
                children=Counter(parents.values()); h=[]
                for v in range(1,n+1):
                    if children[v]: continue
                    path=[v]
                    while path[-1]!=1: path.append(parents[path[-1]])
                    h.append(path)
                changed=rng.choice(list(children)); nw=weights.copy(); nw[changed]=rng.randint(1,55)
                if nw[changed]==weights[changed]: nw[changed]=nw[changed]%55+1
                s=[(weights[v],[-v]) for v in range(1,n+1)]; cs=[(nw[v],[-v]) for v in range(1,n+1)]
                ac,am=laminar_dp(parents,weights,n); bc,bm=laminar_dp(parents,nw,n)
                params=dict(certificate='laminar_tree',parents=parents,weights=weights,changed_vertex=changed,new_weight=nw[changed])
                outputs=[('control',n,h,s,cost_truth(n,h,s,ac,am),None),('challenge',n,h,cs,cost_truth(n,h,cs,bc,bm),dict(type='semantic_shared_repair_cost'))]
            elif sid=='cardinality_projection_encoding':
                primary=rng.randint(6,12); k=rng.randint(2,primary-2); anchor=rng.choice(range(1,primary+1)); sign=rng.choice((-1,1))
                # Independent encodings of the same exactly-k condition.
                a=CardEnc.equals(list(range(1,primary+1)),bound=k,encoding=EncType.seqcounter)
                b=CardEnc.equals(list(range(1,primary+1)),bound=k,encoding=EncType.totalizer)
                selected=set(rng.sample([v for v in range(1,primary+1) if v!=anchor],k-(sign>0)))
                if sign>0: selected.add(anchor)
                added=[]
                for _ in range(rng.randint(2,6)):
                    c=[rng.choice((-1,1))*v for v in rng.sample(range(1,primary+1),3)]
                    if not any((l>0)==(abs(l) in selected) for l in c): c[0]=-c[0]
                    added.append(c)
                primary_hard=exactly(list(range(1,primary+1)),k)+[[anchor*sign]]+added
                projected=evaluate(primary,primary_hard,[])
                h=a.clauses+[[anchor*sign]]+added; ch=b.clauses+[[anchor*sign]]+added
                at=sat_truth(a.nv,h,False); bt=sat_truth(b.nv,ch,False)
                for truth in (at,bt): truth.update(backbone=projected['backbone'],backbone_complete=True,backbone_scope='primary_variables_only',primary_variables=list(range(1,primary+1)),projected_model_count=projected['model_count'])
                params=dict(certificate='cardinality_projection',primary_variables=primary,k=k,anchor=anchor*sign,
                    additional_primary_clauses=added,control_encoding='seqcounter',challenge_encoding='totalizer',pysat_version=importlib.metadata.version('python-sat'))
                outputs=[('control',a.nv,h,[],at,None),('challenge',b.nv,ch,[],bt,dict(type='projected_equivalence',original_variable_map='identity on primary variables'))]
            elif sid=='implied_constraint_amplification':
                n=(50,200,1000,5000)[i%4]+rng.randint(0,5); split=rng.randint(n//3,n*2//3)
                phase=[rng.randrange(2) for _ in range(n)]; edges=[]
                for start,end in ((1,split),(split+1,n)):
                    edges += [(rng.randrange(start,v),v) for v in range(start+1,end+1)]
                h=[c for a,b in edges for c in xor([a,b],phase[a-1]^phase[b-1])]+[[1 if phase[0] else -1]]
                extras=set()
                for _ in range(n):
                    start,end=(1,split) if rng.randrange(2) else (split+1,n)
                    a,b=sorted(rng.sample(range(start,end+1),2)); extras.add((a,b))
                ch=h+[c for a,b in sorted(extras) for c in xor([a,b],phase[a-1]^phase[b-1])]
                model=[v if phase[v-1] else -v for v in range(1,n+1)]; bb=model[:split]
                truth=dict(status='SAT',witness=model,backbone=bb,backbone_complete=True,model_count=2,label_evidence='construction_proved signed-component certificate')
                params=dict(certificate='signed_components',split=split,phase=phase,edges=edges,added_edges=sorted(extras))
                outputs=[('control',n,h,[],truth,None),('challenge',n,ch,[],truth,dict(type='full_model_equivalence'))]
            elif sid in ('soft_weight_partition','objective_integer_scaling','nonempty_constant_offset'):
                n=rng.randint(8,80); parents,weights,h,s=tree_case(rng,n); optimum,model=cover_dp(parents,weights,n)
                params=dict(certificate='tree_cover',parents=parents,weights=weights)
                a=cost_truth(n,h,s,optimum,model)
                if sid=='soft_weight_partition':
                    cs=[]
                    for w,c in s:
                        cut=rng.randint(1,w-1); cs.extend([(cut,c),(w-cut,c)])
                    nn=n; cm=model; oc=optimum; relation=dict(type='pointwise_objective_equivalence')
                elif sid=='objective_integer_scaling':
                    scale=rng.randint(2,25); cs=[(w*scale,c) for w,c in s]; nn=n; cm=model; oc=optimum*scale
                    params['scale']=scale; relation=dict(type='optimum_scaling',factor=scale)
                else:
                    offset=rng.randint(1,50); nn=n+1; cs=s+[(offset,[nn]),(offset,[-nn])]; cm=model+[nn]; oc=optimum+offset
                    params['offset']=offset; relation=dict(type='constant_objective_offset',offset=offset,project_away=[nn])
                outputs=[('control',n,h,s,a,None),('challenge',nn,h,cs,cost_truth(nn,h,cs,oc,cm),relation)]
            elif sid=='general_graph_tseitin':
                v=rng.choice((6,8,12,20,40,80)); seed=rng.randrange(2**32)
                for attempt in range(100):
                    graph=nx.random_regular_graph(3,v,seed=seed+attempt)
                    if nx.is_connected(graph) and not list(nx.bridges(graph)): break
                edges=sorted(tuple(sorted(e)) for e in graph.edges()); n=len(edges); values=[rng.randrange(2) for _ in edges]
                incident={a:[i+1 for i,e in enumerate(edges) if a in e] for a in graph.nodes()}
                charges={a:sum(values[i-1] for i in incident[a])%2 for a in graph.nodes()}; flipped=rng.choice(list(graph.nodes()))
                h=[c for a in sorted(incident) for c in xor(incident[a],charges[a])]
                ch=[c for a in sorted(incident) for c in xor(incident[a],charges[a]^(a==flipped))]
                model=[i if values[i-1] else -i for i in range(1,n+1)]
                truth=dict(status='SAT',witness=model,backbone=[],backbone_complete=True,model_count=2**(n-v+1),label_evidence='construction_proved graph-parity certificate')
                params=dict(certificate='tseitin',vertices=v,edges=edges,charges=charges,flipped_vertex=flipped)
                outputs=[('control',n,h,[],truth,None),('challenge',n,ch,[],dict(status='UNSAT',backbone=None,backbone_complete=True,label_evidence='odd total parity certificate'),dict(type='semantic_parity_change'))]
            elif sid.startswith('cnfgen_'):
                generator_seed=rng.randrange(2**32); random.seed(generator_seed); source=generator_source.copy(); source['lineage_id']=f'{sid}/{i}'
                if sid=='cnfgen_pitfall':
                    v=rng.choice((6,8,10,12,16,20)); ny=rng.randint(2,8); nz=rng.randint(2,7); k=rng.choice((2,4))
                    formula=PitfallFormula(v,3,ny,nz,k); params=dict(certificate='cnfgen_unsat',generator='PitfallFormula',args=[v,3,ny,nz,k])
                elif sid in ('cnfgen_pebbling','cnfgen_stone'):
                    v=rng.randint(10,90) if sid=='cnfgen_pebbling' else rng.randint(5,18)
                    dag=nx.DiGraph(); dag.add_nodes_from(range(1,v+1)); dag.add_edges_from((j,j+1) for j in range(1,v))
                    for _ in range(v//2):
                        a,b=sorted(rng.sample(range(1,v+1),2)); dag.add_edge(a,b)
                    if sid=='cnfgen_pebbling': formula=PebblingFormula(dag)
                    else: stones=rng.randint(2,6); formula=StoneFormula(dag,stones)
                    params=dict(certificate='cnfgen_unsat',generator='PebblingFormula' if sid=='cnfgen_pebbling' else 'StoneFormula',dag_edges=sorted(dag.edges()),vertices=v)
                    if sid=='cnfgen_stone': params['stones']=stones
                else:
                    m=rng.randint(6,35); graph=nx.Graph(); left=list(range(m)); right=list(range(m,2*m)); graph.add_nodes_from(left,bipartite=0); graph.add_nodes_from(right,bipartite=1)
                    # Three cyclic perfect matchings form a 3-regular simple graph; shuffle one partition to vary labeled incidence.
                    perm=rng.sample(right,m); shifts=rng.sample(range(1,m),2)
                    for a in left:
                        for shift in (0,*shifts): graph.add_edge(a,perm[(a+shift)%m])
                    formula=SubsetCardinalityFormula(graph); params=dict(certificate='cnfgen_unsat',generator='SubsetCardinalityFormula',partition_size=m,edges=sorted(graph.edges()))
                n=formula.number_of_variables(); h=[list(c) for c in formula]; params['generator_seed']=generator_seed
                if sid=='cnfgen_pitfall':
                    # Upstream uses sign*first_edge + lit - 1. Negative literals are two positions too far.
                    # Correct only the copied Tseitin hard part; every Z guard is positive.
                    upstream=serialize(n,h,[],'cnf'); original=ROOT/'sources'/'originals'/'cnfgen-pitfall-unadapted'/f'{i:04d}.cnf'
                    original.parent.mkdir(parents=True,exist_ok=True); original.write_bytes(upstream)
                    source.update(original_path=original.relative_to(ROOT).as_posix(),original_sha256=sha(upstream),
                        generator_adaptation='MATT signed-edge-offset correction; upstream package remains unchanged')
                    hard_part=4*v*k
                    assert all(len(c)==3+nz for c in h[:hard_part])
                    h=[[lit+2 if ci<hard_part and lit<0 else lit for lit in clause] for ci,clause in enumerate(h)]
                    params['generator_patch']='signed_edge_offset_v1: negative hard-part edge literals shifted +2'
                truth=dict(status='UNSAT',backbone=None,backbone_complete=True,label_evidence='documented construction; independent solver validation recorded separately')
                if sid=='cnfgen_pebbling':
                    control=[c for c in h if c!=[-v]]; assert len(control)==len(h)-1
                    outputs=[('control',n,control,[],dict(status='SAT',witness=all_model(n),backbone=list(range(1,n+1)),backbone_complete=True,model_count=1,label_evidence='source propagation certificate'),None),('challenge',n,h,[],truth,dict(type='sink_contradiction'))]
                else: outputs=[('original',n,h,[],truth,None)]
            elif sid=='model_rb_hidden_optimum':
                groups=rng.randint(6,35); domain=rng.randint(4,18); n=groups*domain; planted=[g*domain+rng.randrange(domain)+1 for g in range(groups)]
                forbidden=set()
                for g in range(groups): forbidden.update(itertools.combinations(range(g*domain+1,(g+1)*domain+1),2))
                within=sorted(forbidden); extras=set()
                for _ in range(int(groups*math.log(groups)*domain)):
                    a,b=sorted(rng.sample(range(1,n+1),2))
                    if (a-1)//domain!=(b-1)//domain and not (a in planted and b in planted): extras.add((a,b))
                mid=len(extras)//2; cross=sorted(extras); weight=n+1
                s=[(1,[v]) for v in range(1,n+1)]+[(weight,[-a,-b]) for a,b in within+cross[:mid]]
                cs=[(1,[v]) for v in range(1,n+1)]+[(weight,[-a,-b]) for a,b in within+cross]
                model=[v if v in planted else -v for v in range(1,n+1)]; opt=n-groups
                params=dict(certificate='model_rb',groups=groups,domain=domain,planted=planted,penalty=weight)
                source=dict(url='https://rb-bench.github.io/benchmarks/weighted-max2sat.html',adaptation='independently seeded published group/forbidden-pair model',lineage_id=f'{sid}/{i}')
                outputs=[('control',n,[],s,cost_truth(n,[],s,opt,model),None),('challenge',n,[],cs,cost_truth(n,[],cs,opt,model),dict(type='planted_optimum_preserving_constraints'))]
            elif sid.startswith('neural_'):
                n=rng.randint(20,65); sat,unsat=neural_pair(rng,n); source=neural_source.copy(); source['lineage_id']=f'{sid}/{i}'
                if sid=='neural_sat_witness_perturbation':
                    h=sat; base=sat_truth(n,h,True); witness=set(base['witness']); added=[]
                    for _ in range(max(3,len(h)//20)):
                        c=[rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),3)]
                        if not any(l in witness for l in c): c[0]=-c[0]
                        added.append(c)
                    ch=h+added; truth=sat_truth(n,ch,True); params=dict(certificate='sat_witness',added_clauses=added)
                else:
                    h=unsat; base=dict(status='UNSAT',backbone=None,backbone_complete=True,label_evidence='MiniSat22 first-conflict construction')
                    if sid=='neural_unsat_literal_deletion':
                        ch=[c[:] for c in h]; edits=[]
                        for ci in rng.sample(range(len(ch)),max(2,len(ch)//20)):
                            if len(ch[ci])>1: removed=ch[ci].pop(rng.randrange(len(ch[ci]))); edits.append([ci,removed])
                        params=dict(certificate='unsat_literal_strengthening',edits=edits)
                    else:
                        added=[[rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),3)] for _ in range(max(3,len(h)//20))]
                        ch=h+added; params=dict(certificate='unsat_clause_addition',added_clauses=added)
                    truth=base.copy()
                outputs=[('control',n,h,[],base,None),('challenge',n,ch,[],truth,dict(type='status_preserving_perturbation'))]
            else: raise ValueError(sid)
            # Uniqueness is checked on actual mathematical cores, with no disjoint filler variables.
            fingerprint=sha(json.dumps([[nn,sorted(sorted(c) for c in hh),sorted((w,sorted(c)) for w,c in ss)] for _,nn,hh,ss,_,_ in outputs],separators=(',',':')).encode())
            if fingerprint in fingerprints: raise RuntimeError(f'Duplicate generated core: {sid}/{i}')
            fingerprints.add(fingerprint)
            params['no_disjoint_filler']=True
            for variant,nn,h,s,truth,relation in outputs: emit(rows,spec,i,variant,nn,h,s,truth,params,source,relation)
        entry=spec.copy(); entry.update(groups=COUNT,examples=len(rows)-before,distinct_core_groups=len(fingerprints)); catalogue.append(entry)
        write_rows(ROOT/'parts'/'extensions.jsonl',rows); write_json(ROOT/'parts'/'extension-scenarios.json',catalogue)
        print(f'Built {sid}: {COUNT} distinct cores, {len(rows)-before} formulas',flush=True)
    write_json(ROOT/'parts'/'extension-generator-versions.json',dict(cnfgen=importlib.metadata.version('CNFgen'),networkx=nx.__version__,pysat=importlib.metadata.version('python-sat')))


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--resume',action='store_true'); ap.add_argument('--only',nargs='+'); args=ap.parse_args(); build(args.resume,args.only)
