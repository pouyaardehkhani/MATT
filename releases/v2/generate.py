"""MATT v2: mathematical adversarial SAT/MaxSAT pairs, with exhaustive truth labels.

No baseline is imported or executed. Python standard library suffices to generate.
Run verify.py for a fresh exhaustive audit and an optional independent PySAT audit.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import random
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 20261016
VERSION = "2.0.0"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@lru_cache(maxsize=20)
def universe(n):
    # Assignment index m uses bit v-1 for variable v. Each int is a truth table.
    count = 1 << n
    full = (1 << count) - 1
    masks = []
    for j in range(n):
        step = 1 << j
        block = ((1 << step) - 1) << step
        masks.append(block * (full // ((1 << (2 * step)) - 1)))
    return full, masks


def clause_mask(clause, full, masks):
    result = 0
    for lit in clause:
        bits = masks[abs(lit) - 1]
        result |= bits if lit > 0 else full ^ bits
    return result


def model_from_index(index, n):
    return [v if index & (1 << (v - 1)) else -v for v in range(1, n + 1)]


def evaluate(n, hard, soft):
    """Exact exhaustive evaluation via bit-sliced addition, independent of SAT code."""
    full, masks = universe(n)
    feasible = full
    for c in hard:
        feasible &= clause_mask(c, full, masks)
    if not feasible:
        return {"status": "UNSAT", "model_count": 0, "backbone": None}
    backbone = []
    for v, bits in enumerate(masks, 1):
        if feasible & bits == feasible:
            backbone.append(v)
        elif not feasible & bits:
            backbone.append(-v)
    result = {"status": "SAT", "model_count": feasible.bit_count(), "backbone": backbone}
    if not soft:
        idx = (feasible & -feasible).bit_length() - 1
        result["witness"] = model_from_index(idx, n)
        return result
    width = sum(w for w, _ in soft).bit_length() + 1
    planes = [0] * width
    for weight, c in soft:
        violated = feasible & (full ^ clause_mask(c, full, masks))
        for bit in range(weight.bit_length()):
            if not weight & (1 << bit):
                continue
            carry = violated
            pos = bit
            while carry:
                old = planes[pos]
                planes[pos] = old ^ carry
                carry &= old
                pos += 1
    optima = feasible
    cost = 0
    for bit in reversed(range(width)):
        zero = optima & (full ^ planes[bit])
        if zero:
            optima = zero
        else:
            cost |= 1 << bit
    idx = (optima & -optima).bit_length() - 1
    result.update(status="OPTIMUM", optimum=cost, optimal_model_count=optima.bit_count(),
                  witness=model_from_index(idx, n))
    return result


def xor(vars_, parity):
    # Every clause excludes one assignment having the wrong parity.
    return [[-v if b else v for v, b in zip(vars_, bits)]
            for bits in itertools.product((0, 1), repeat=len(vars_)) if sum(bits) % 2 != parity]


def atmost(vs, k):
    return [[-v for v in subset] for subset in itertools.combinations(vs, k + 1)]


def atleast(vs, k):
    return [list(subset) for subset in itertools.combinations(vs, len(vs) - k + 1)]


def exactly(vs, k):
    return atmost(vs, k) + atleast(vs, k)


def eq(a, b):
    return [[-a, b], [a, -b]]


def force(lit, aux):
    return [[lit, aux], [lit, -aux]]


def graph(rng, n):
    edges = {(i, i + 1) for i in range(1, n)}
    edges |= {(i, j) for i in range(1, n + 1) for j in range(i + 2, n + 1) if rng.random() < .3}
    return sorted(edges)


# Each catalogue entry is a construction hypothesis, not an assertion of a baseline defect.
SPECS = [
 ("rare_escape", "cnf", "Rare countermodel closed by a trigger", "A selector s normally agrees with an output x; the opposite branch requires every trigger bit to be true.", "Add one clause forbidding the all-true trigger.", "Model sampling can confuse a highly biased literal with a backbone. Closing the escape makes it genuinely forced.", "(s OR t_i) for all i, x <-> s; intervention: OR_i NOT t_i."),
 ("implication_reversal", "cnf", "Reconvergent implication orientation", "A connected equality network carries a hidden anchor through many paths.", "Reverse the anchor polarity while keeping the network.", "A cached or partially propagated backbone must change sign throughout the component.", "x_i <-> x_j on a connected graph; (a OR q) AND (a OR NOT q), then a becomes NOT a."),
 ("parity_cycle", "cnf", "One parity sign changes consistency", "Pairwise XOR relations close a cycle whose XOR sum is zero.", "Flip the parity on the closing edge.", "Local consistency of individual clauses does not establish global satisfiability.", "XOR_i (x_i XOR x_(i+1)) = 0; one RHS flip makes it 1."),
 ("parity_pin", "cnf", "Free parity mode becomes a full backbone", "A signed equality tree has two complementary solutions.", "Pin one variable with a two-clause anchor.", "A single semantic intervention forces an entire correlated component.", "x_i XOR x_parent(i) = b_i; add (x_1 OR q) AND (x_1 OR NOT q)."),
 ("cardinality_boundary", "cnf", "Overlapping cardinality contradiction", "A resource pool requires exactly k active items.", "Add an at-least-(k+1) requirement on the same pool.", "Different cardinality constraints look individually feasible but jointly contradict one another.", "sum x_i = k versus sum x_i = k AND sum x_i >= k+1."),
 ("unique_witness_block", "cnf", "Blocking a globally unique witness", "A signed connected network plus an anchor has exactly one core assignment.", "Add one clause falsified by that complete core assignment.", "A long added clause can eliminate the last model despite leaving every variable well formed.", "F has unique core model m; F AND (OR_i NOT m_i) has none."),
 ("broken_exchange", "cnf", "Nearly exchangeable choices", "Exactly one interchangeable option is chosen.", "Forbid one option using a relation to a fresh signal rather than changing the format.", "A symmetry assumption from the control becomes invalid; one variable enters the backbone.", "sum x_i = 1; add (NOT x_j OR z) AND (NOT x_j OR NOT z)."),
 ("complement_orientation", "cnf", "Signed symmetry loses one orientation", "Variables in two classes are equal within a class and opposite across classes.", "Add a disjunction containing literals true in only one orientation.", "Polarity-aware symmetry and backbone logic must distinguish the two complementary models.", "x_i XOR x_j = phase_i XOR phase_j; add a clause selecting one phase."),
 ("conditional_exchange", "cnf", "Conditional symmetry is not global symmetry", "Each choice x_i has its own indicator y_i; options initially exchange together.", "Add a cross-condition coupling one option to a different indicator.", "Exchanging only the option variables or reusing a former global symmetry can delete valid solutions.", "sum x_i=1, y_i <-> x_i; add NOT x_a OR y_b for a != b."),
 ("bipartite_frustration", "cnf", "A graph becomes non-bipartite", "Two-color constraints lie on a connected bipartite graph.", "Add an edge within one color class.", "One local edge creates a global odd-cycle obstruction.", "For each edge enforce x_u XOR x_v=1; the extra edge closes an odd cycle."),
 ("hall_deficiency", "cnf", "Hidden resource bottleneck", "A bipartite assignment graph admits a perfect matching.", "Restrict two agents to the same single resource.", "Per-agent availability is nonempty but the joint resource allocation is impossible.", "Exactly one edge per agent, at most one per resource; |N({a,b})|=1<2."),
 ("color_obstruction", "cnf", "Color symmetry with a local obstruction", "A triangle and an extra vertex admit three colors.", "Connect the extra vertex to every triangle vertex.", "The same color permutations remain available, but the extra clique makes the formula UNSAT.", "3-color K3 plus v; intervention completes K4, which needs four colors."),
 ("reconvergent_circuit", "cnf", "Circuit output phase intervention", "A random acyclic AND/OR/XOR circuit has a planted, fixed input vector and reconvergent paths.", "Change the required output from its implied value to its opposite.", "Reasoning from local fan-in or an incomplete circuit abstraction can miss the unique output consequence.", "Inputs fixed by two-clause anchors; Tseitin gate equivalences; assert output b versus NOT b."),
 ("component_bridge", "cnf", "A bridge correlates formerly independent components", "Two signed connected components each have two orientations.", "Add one parity bridge between the components.", "Component decomposition must be updated after the intervention; model count halves without necessarily creating a backbone.", "F(X) AND G(Y), then AND (x_1 XOR y_1=b)."),
 ("complete_conflict", "cnf", "Last missing conflict clause", "All assignments of a small variable block except one are excluded by full-width clauses.", "Insert the single omitted conflict clause.", "The last globally surviving witness disappears although there is no empty clause or direct contradictory-unit pair.", "All 2^k full-width clauses except C_m versus all 2^k clauses."),
 ("conditional_threshold", "cnf", "Threshold trigger forces a selector", "When selector s is false, a pool must have exactly k selected bits; when true the pool is unrestricted.", "Raise the guarded lower threshold by one.", "Only the trigger branch becomes impossible, creating a selector backbone without making the whole instance UNSAT.", "(s OR CNF(sum x_i<=k)) AND (s OR CNF(sum x_i>=k)); raise lower bound to k+1."),
 ("ferromagnetic_barrier", "wcnf", "Suboptimal one-flip basin with a strict core", "Coupled Boolean choices have a cheap all-true basin and an expensive all-false basin.", "Increase equality-coupling weight above the total unary preference weight.", "A one-flip improving search can remain at a proven suboptimal feasible assignment; the objective is ordinary integer MaxSAT.", "Soft J*[x_i=x_j], positive units total P, negative anchor B<P. All-true costs B; all-false costs P; J>P+B blocks every core-variable flip."),
 ("feasible_exchange_barrier", "wcnf", "Disconnected feasible orientations", "A connected hard equality component has two feasible assignments with unequal costs.", "Turn soft coupling constraints into hard equalities.", "Changing basin requires temporary hard-constraint violations; a feasible incumbent can be suboptimal.", "Hard x_i=x_j; soft positive units total P and negative anchor B<P."),
 ("weighted_majority", "wcnf", "Clause majority disagrees with weight majority", "Many linked positive proxy preferences compete with one negative preference.", "Move the negative weight from just below to just above their total.", "Choosing the most numerous satisfied clauses gives the wrong weighted optimum after the intervention.", "Hard y_i=x; soft (y_i,1), (NOT x,q); optimum min(m,q), winning orientation reverses at q=m."),
 ("vertex_cover_star", "wcnf", "Coordinated star-cover exchange", "A star graph can be covered by its center or all leaves, with variable selection costs.", "Move center cost across the total leaf cost.", "Greedy single-vertex deletion cannot exchange the two covers while staying feasible.", "Hard (c OR l_i); soft NOT c cost W, NOT l_i cost w_i; optimum min(W,sum_i w_i)."),
 ("weighted_parity_frustration", "wcnf", "Frustrated weighted cycle", "Weighted parity preferences form a consistent cycle.", "Flip the closing parity relation.", "The inconsistent cycle must pay at least one edge weight; sacrificing the wrong edge is a measurable cost gap.", "Soft XOR edge relations, same weight for their two CNF clauses; odd parity inconsistency costs the minimum edge weight."),
 ("overlapping_cores", "wcnf", "Shared exclusion cores", "Positive vertex preferences compete under pairwise exclusion constraints.", "Add overlapping exclusions around a high-degree vertex.", "Counting overlapping conflicts independently can overestimate a lower bound or choose poor relaxations.", "Hard NOT x_u OR NOT x_v; soft (x_v,w_v): optimum = total weights minus maximum-weight independent set."),
 ("weighted_hitting_set", "wcnf", "Shared repair covers many demands", "Each demand is a disjunction of possible repairs, each with an activation cost.", "Add one shared repair to several demands.", "Repairing each demand independently misses savings from one shared activation.", "Hard OR_{v in S_j} x_v; soft (NOT x_v,w_v): minimum-weight hitting set."),
 ("capacity_weight_swap", "wcnf", "Capacity threshold and close weights", "At most k rewards can be selected.", "Raise a formerly excluded item's weight above a selected item's weight.", "A stale ranking or an overaggressive weight bucket keeps a feasible but suboptimal solution.", "Hard sum x_i<=k; soft (x_i,w_i); optimum is sum of the n-k smallest weights."),
 ("exact_cardinality_exchange", "wcnf", "No feasible single-bit move", "Exactly k choices must remain active, with weighted rewards.", "Add weak pairwise agreement preferences to change the best exchange.", "Every one-bit change violates feasibility; improvement requires a coordinated two-bit exchange or temporary infeasibility.", "Hard sum x_i=k; soft unary rewards plus equality preferences on selected random pairs."),
 ("residual_weight_reversal", "wcnf", "Small residual after competing preferences", "Opposite soft preferences on a hard-linked component mostly cancel.", "Change one weight by a small amount across the residual balance point.", "Dropping a residual or forgetting a constant cost can reverse the optimum or misreport its value.", "Hard y_i=x; soft (x,a),(NOT x,b),(y_i,c_i); compare b with a+sum c_i."),
 ("hierarchical_tradeoff", "wcnf", "One high priority trades against many lower priorities", "Exactly one of two assignment bundles is feasible.", "Change the high-level preference across the total lower-level loss.", "Treating finite weights as absolute priorities changes the actual weighted problem.", "Hard bundle equivalences/oppositions; soft lower rewards sum L versus a high preference of weight L-1 or L+1."),
 ("cost_component_bridge", "wcnf", "Coupling breaks objective additivity", "Two independently optimized bundles prefer opposite orientations.", "Add one hard equality across the bundles.", "The sum of old component optima is no longer achievable after coupling.", "min f(X)+min g(Y) becomes min_{x_1=y_1}(f(X)+g(Y))."),
 ("last_soft_conflict", "wcnf", "A complete weighted conflict cover", "Full-width soft clauses exclude every core assignment except one.", "Insert the omitted soft clause with a positive weight.", "The optimum changes from zero to the least clause weight, so a stale zero-cost model is invalid.", "Each full-width clause is false at exactly one assignment; after all 2^k are present OPT=min_C w_C."),
 ("spin_glass_intervention", "wcnf", "Competing signed pair interactions", "A connected graph mixes weighted equality, inequality, and unary preferences.", "Flip the preferred relation on one influential edge.", "A local sign change can rearrange the global optimum; local edge satisfaction alone is insufficient.", "Minimize sum_e w_e*[x_u XOR x_v != b_e] plus unary penalties."),
 ("conjunction_trigger", "wcnf", "A conjunction trigger disables the cheap branch", "A selector controls two feasible cost basins and is linked to a multi-bit trigger.", "Require all trigger bits, thereby forcing the more expensive selector orientation.", "A semantic trigger changes the feasible optimum rather than the input syntax; cached incumbents must be rechecked.", "t_1 AND ... AND t_k -> s; s=false costs B, s=true costs P>B; add hard t_i=true."),
 ("hard_priority_lure", "wcnf", "Very attractive infeasible assignment", "A hard capacity constraint rules out selecting every profitable item.", "Add a hard exclusion between two high-reward items.", "Soft improvement must never be reported as a feasible solution if it violates even one hard constraint.", "Hard sum x_i<=k plus NOT x_a OR NOT x_b; soft (x_i,w_i). All weights remain small and positive."),
]


def build(sid, rng, index):
    """Return n, control hard/soft, challenge hard/soft, and semantic parameters."""
    hard, soft = [], []
    ch, cs = None, None
    p = {}
    n = rng.randint(5, 8)
    vs = list(range(1, n + 1))
    if sid == "rare_escape":
        k = rng.randint(4, 8); n = k + 2
        hard = [[1, t] for t in range(3, n + 1)] + eq(1, 2)
        ch = hard + [[-t for t in range(3, n + 1)]]
        p = {"trigger_width": k, "rare_branch_core_models": 1, "usual_branch_core_models": 2**k}
    elif sid in ("implication_reversal", "parity_pin", "unique_witness_block", "complement_orientation"):
        phase = [rng.randrange(2) for _ in vs]
        edges = graph(rng, n)
        hard = [c for a, b in edges for c in xor([a, b], phase[a-1] ^ phase[b-1])]
        if sid in ("implication_reversal", "unique_witness_block"):
            n += 1; anchor = 1 if phase[0] else -1
            network = hard[:]; hard += force(anchor, n)
            ch = network + force(-anchor, n) if sid == "implication_reversal" else hard + [[-v if phase[v-1] else v for v in vs]]
        elif sid == "parity_pin":
            n += 2; hard += eq(n-1,n); ch = hard + force(1, n)
        else:
            ch = hard + [[v if phase[v-1] else -v for v in rng.sample(vs, 3)]]
        p = {"phase": phase, "edges": edges}
    elif sid in ("parity_cycle", "weighted_parity_frustration"):
        phase = [rng.randrange(2) for _ in vs]
        rels = [(i, i % n + 1, phase[i-1] ^ phase[i % n]) for i in vs]
        if sid == "parity_cycle":
            hard = [c for a,b,t in rels for c in xor([a,b],t)]
            ch = [c for a,b,t in rels[:-1] for c in xor([a,b],t)] + xor([n,1], rels[-1][2]^1)
        else:
            weights = [rng.randint(1,19) for _ in rels]
            soft = [(w,c) for (a,b,t),w in zip(rels,weights) for c in xor([a,b],t)]
            cs = soft[:-2] + [(weights[-1],c) for c in xor([n,1],rels[-1][2]^1)]
            p["edge_weights"] = weights
        p["cycle_relations"] = rels
    elif sid == "cardinality_boundary":
        k = rng.randint(2,n-2); hard = exactly(vs,k); ch = hard + atleast(vs,k+1); p={"k":k}
    elif sid in ("broken_exchange", "conditional_exchange"):
        if sid == "broken_exchange":
            hard = exactly(vs,1); a = rng.choice(vs); n += 2; hard += eq(n-1,n)
            ch = hard + force(-a,n); p={"forbidden_option":a}
        else:
            n = rng.randint(3,5); vs=list(range(1,n+1)); m=n; n*=2
            hard = exactly(vs,1) + [c for v in vs for c in eq(v,v+m)]
            a,b=rng.sample(vs,2); ch=hard+[[-a,b+m]]; p={"coupled_options":[a,b]}
    elif sid == "bipartite_frustration":
        n=rng.randint(5,9); split=rng.randint(2,n-2)
        left=list(range(1,split+1)); right=list(range(split+1,n+1))
        edges={(1,b) for b in right}|{(a,right[0]) for a in left}
        edges|={(a,b) for a in left for b in right if rng.random()<.4}
        hard=[c for a,b in sorted(edges) for c in xor([a,b],1)]
        a,b=rng.sample(left,2); ch=hard+xor([a,b],1); p={"edges":sorted(edges),"extra_edge":[a,b]}
    elif sid == "hall_deficiency":
        m=rng.randint(3,4); n=m*m
        def v(a,b): return a*m+b+1
        allowed={(a,a) for a in range(m)}|{(a,b) for a in range(m) for b in range(m) if rng.random()<.65}
        core=[c for a in range(m) for c in exactly([v(a,b) for b in range(m)],1)]
        core += [c for b in range(m) for c in atmost([v(a,b) for a in range(m)],1)]
        hard=core+[[-v(a,b)] for a in range(m) for b in range(m) if (a,b) not in allowed]
        resource=rng.randrange(m); ch=hard+[[-v(a,b)] for a in (0,1) for b in range(m) if b!=resource]
        p={"agents":m,"allowed_edges":sorted(allowed),"bottleneck_resource":resource}
    elif sid == "color_obstruction":
        n=12
        def cols(a): return list(range(3*a+1,3*a+4))
        core=[c for a in range(4) for c in exactly(cols(a),1)]
        edges=[(0,1),(1,2),(0,2)]
        extra=rng.sample([0,1,2],rng.randint(0,2))
        hard=core+[[-cols(a)[k],-cols(b)[k]] for a,b in edges+[(3,b) for b in extra] for k in range(3)]
        ch=core+[[-cols(a)[k],-cols(b)[k]] for a,b in edges+[(3,b) for b in range(3)] for k in range(3)]
        p={"control_extra_neighbors":extra,"colors":3}
    elif sid == "reconvergent_circuit":
        inputs=rng.randint(3,4); gates=rng.randint(3,5); n=inputs+gates+1; aux=n
        vals={i:rng.randrange(2) for i in range(1,inputs+1)}
        hard=[c for i,b in vals.items() for c in force(i if b else -i,aux)]
        desc=[]
        for out in range(inputs+1,inputs+gates+1):
            a,b=rng.sample(range(1,out),2); op=rng.choice(["and","or","xor"])
            if op=="and": enc=[[-out,a],[-out,b],[out,-a,-b]]; val=vals[a]&vals[b]
            elif op=="or": enc=[[out,-a],[out,-b],[-out,a,b]]; val=vals[a]|vals[b]
            else: enc=xor([a,b,out],0); val=vals[a]^vals[b]
            hard+=enc; vals[out]=val; desc.append([out,op,a,b])
        last=inputs+gates; lit=last if vals[last] else -last
        ch=hard+[[-lit]]; hard=hard+[[lit]]; p={"gates":desc,"input_values":{str(i):vals[i] for i in range(1,inputs+1)}}
    elif sid == "component_bridge":
        n=rng.randint(6,10); split=rng.randint(3,n-3)
        phase=[rng.randrange(2) for _ in range(n)]
        edges=[(i,i+1) for i in range(1,n) if i!=split]
        hard=[c for a,b in edges for c in xor([a,b],phase[a-1]^phase[b-1])]
        parity=rng.randrange(2); ch=hard+xor([1,split+1],parity); p={"split":split,"bridge_parity":parity,"phase":phase}
    elif sid in ("complete_conflict","last_soft_conflict"):
        n=rng.randint(3,7); assignment=rng.randrange(1<<n)
        clauses=[[(-v if mask & (1<<(v-1)) else v) for v in range(1,n+1)] for mask in range(1<<n)]
        if sid=="complete_conflict": hard=[c for i,c in enumerate(clauses) if i!=assignment]; ch=clauses
        else:
            weights=[rng.randint(1,23) for _ in clauses]
            soft=[(weights[i],c) for i,c in enumerate(clauses) if i!=assignment]; cs=soft+[(weights[assignment],clauses[assignment])]
            p["weights"]=weights
        p["omitted_assignment"]=model_from_index(assignment,n)
    elif sid=="conditional_threshold":
        k=rng.randint(2,n-2); n+=1; sel=n
        hard=[[sel]+c for c in atmost(vs,k)+atleast(vs,k)]
        ch=[[sel]+c for c in atmost(vs,k)+atleast(vs,k+1)]; p={"k":k,"selector":sel}
    elif sid in ("ferromagnetic_barrier","feasible_exchange_barrier"):
        if sid=="ferromagnetic_barrier" and index==0: n=3; vs=[1,2,3]; weights=[3,3,3]; b=7
        else: weights=[rng.randint(2,6) for _ in vs]; b=rng.randint(1,sum(weights)-1)
        total=sum(weights); edges=graph(rng,n); j=total+b+1
        unary=[(w,[v]) for v,w in zip(vs,weights)]+[(b,[-1])]
        soft=unary+[(1,c) for a,z in edges for c in eq(a,z)]
        if sid=="ferromagnetic_barrier": cs=unary+[(j,c) for a,z in edges for c in eq(a,z)]
        else: cs=unary; ch=[c for a,z in edges for c in eq(a,z)]
        p={"edges":edges,"positive_weights":weights,"P":total,"B":b,"coupling":j,
           "trap_core_assignment":[-v for v in vs],"optimal_core_assignment":vs,"core_variables":n}
    elif sid=="weighted_majority":
        n=rng.randint(5,10); hard=[c for i in range(2,n+1) for c in eq(1,i)]
        soft=[(1,[i]) for i in range(2,n+1)]+[(n-2,[-1])]
        cs=soft[:-1]+[(n,[-1])]; p={"proxy_count":n-1,"negative_weights":[n-2,n]}
    elif sid=="vertex_cover_star":
        weights=[rng.randint(1,8) for _ in range(n-1)]; total=sum(weights); delta=rng.randint(1,min(total-1,4))
        hard=[[1,v] for v in range(2,n+1)]; soft=[(w,[-v]) for v,w in zip(range(2,n+1),weights)]+[(total+delta,[-1])]
        cs=soft[:-1]+[(total-delta,[-1])]; p={"leaf_weights":weights,"center_costs":[total+delta,total-delta]}
    elif sid=="overlapping_cores":
        edges={(i,i+1) for i in range(1,n,2)}; added={(1,3)}|{(1,j) for j in range(4,n+1) if rng.random()<.8}
        hard=[[-a,-b] for a,b in sorted(edges)]; ch=hard+[[-a,-b] for a,b in sorted(added)]
        soft=[(rng.randint(1,15),[v]) for v in vs]; p={"exclusions":sorted(edges),"added_exclusions":sorted(added)}
    elif sid=="weighted_hitting_set":
        demands=[sorted(rng.sample(range(2,n+1),rng.randint(2,min(4,n-1)))) for _ in range(rng.randint(3,6))]
        hard=demands+[[1,2]]; ch=[[1]+c for c in demands]+[[1,2]]
        soft=[(rng.randint(1,12),[-v]) for v in vs]; p={"demands":demands,"shared_repair":1}
    elif sid in ("capacity_weight_swap","exact_cardinality_exchange","hard_priority_lure"):
        k=rng.randint(2,n-2); weights=rng.sample(range(2,45),n)
        hard=exactly(vs,k) if sid=="exact_cardinality_exchange" else atmost(vs,k)
        soft=[(w,[v]) for v,w in zip(vs,weights)]
        if sid=="capacity_weight_swap":
            rank=sorted(vs,key=lambda v:weights[v-1],reverse=True); raised=rank[-1]
            new=weights[rank[k-1]-1]+1; cs=[(new if v==raised else w,[v]) for v,w in zip(vs,weights)]
            p={"raised_variable":raised,"new_weight":new}
        elif sid=="exact_cardinality_exchange":
            edges=graph(rng,n); cs=soft+[(rng.randint(1,5),c) for a,b in edges for c in eq(a,b)]; p={"preference_edges":edges}
        else:
            a,b=sorted(vs,key=lambda v:weights[v-1],reverse=True)[:2]; ch=hard+[[-a,-b]]; p={"excluded_pair":[a,b]}
        p.update(k=k,weights=weights)
    elif sid=="residual_weight_reversal":
        hard=[c for i in range(2,n+1) for c in eq(1,i)]; weights=[rng.randint(1,6) for _ in range(n-1)]; a=rng.randint(4,20); total=a+sum(weights)
        soft=[(a,[1])]+[(w,[i]) for i,w in zip(range(2,n+1),weights)]+[(total-1,[-1])]
        cs=soft[:-1]+[(total+1,[-1])]; p={"positive_total":total,"negative_weights":[total-1,total+1]}
    elif sid=="hierarchical_tradeoff":
        low=[rng.randint(2,9) for _ in range(n-1)]; total=sum(low)
        hard=[c for i in range(2,n+1) for c in xor([1,i],1)]
        soft=[(w,[i]) for i,w in zip(range(2,n+1),low)]+[(total-1,[1])]
        cs=soft[:-1]+[(total+1,[1])]; p={"lower_total":total,"high_weights":[total-1,total+1]}
    elif sid=="cost_component_bridge":
        n=rng.randint(6,10); split=rng.randint(3,n-3)
        hard=[c for i in range(1,n) if i!=split for c in eq(i,i+1)]
        soft=[(rng.randint(2,8),[i if i<=split else -i]) for i in range(1,n+1)]
        # Nonzero baseline cost with ordinary opposite preferences.
        soft += [(1,[-1]),(1,[split+1])]
        ch=hard+eq(1,split+1); p={"split":split}
    elif sid=="spin_glass_intervention":
        edges=graph(rng,n); rel=[(a,b,rng.randrange(2),rng.randint(1,13)) for a,b in edges]
        soft=[(w,c) for a,b,t,w in rel for c in xor([a,b],t)]+[(rng.randint(1,5),[rng.choice([-1,1])*v]) for v in vs]
        a,b,t,w=rel[0]; cs=[(w,c) for c in xor([a,b],t^1)]+soft[2:]; p={"relations":rel,"flipped_edge":[a,b]}
    elif sid=="conjunction_trigger":
        n=rng.randint(6,10); trigger=list(range(2,n+1)); b=rng.randint(2,8); total=b+rng.randint(2,10)
        hard=[[-v for v in trigger]+[1]]
        soft=[(total,[-1]),(b,[1])]; ch=hard+[[v] for v in trigger]
        p={"trigger_variables":trigger,"cheap_cost":b,"triggered_cost":total}
    else:
        raise ValueError(sid)
    ch = hard[:] if ch is None else ch
    cs = soft[:] if cs is None else cs
    # Random satisfiable context varies genuine formula structure as well as core parameters.
    # It is disjoint, identical within a pair, and has no objective contribution.
    context_n = rng.randint(2, min(4,18-n)); context_vars=list(range(n+1,n+context_n+1))
    planted={v:rng.choice([-1,1])*v for v in context_vars}
    pool=[]
    for width in range(2,context_n+1):
        for subset in itertools.combinations(context_vars,width):
            for signs in itertools.product((-1,1),repeat=width):
                c=[v*s for v,s in zip(subset,signs)]
                if any(lit==planted[abs(lit)] for lit in c): pool.append(c)
    context=rng.sample(pool,rng.randint(1,min(len(pool),8)))
    if {abs(lit) for c in context for lit in c} != set(context_vars):
        context.append(list(planted.values()))
    p.update(core_nvars=n,context_nvars=context_n,context_clauses=context)
    return n+context_n,hard+context,soft,ch+context,cs,p


def transformed(n, hard, soft, rng):
    perm=rng.sample(range(1,n+1),n); signs=[rng.choice([-1,1]) for _ in perm]
    mapping={v:perm[v-1]*signs[v-1] for v in range(1,n+1)}
    def clause(c):
        result=[mapping[abs(l)]*(1 if l>0 else -1) for l in c]; rng.shuffle(result); return result
    h=[clause(c) for c in hard]; s=[(w,clause(c)) for w,c in soft]; rng.shuffle(h); rng.shuffle(s)
    return h,s,mapping


def serialize(n, hard, soft, family):
    if family=="cnf":
        lines=[f"p cnf {n} {len(hard)}"]+[" ".join(map(str,c))+" 0" for c in hard]
    else:
        top=sum(w for w,_ in soft)+1
        lines=[f"p wcnf {n} {len(hard)+len(soft)} {top}"]
        lines += [f"{top} "+" ".join(map(str,c))+" 0" for c in hard]
        lines += [f"{w} "+" ".join(map(str,c))+" 0" for w,c in soft]
    return ("\n".join(lines)+"\n").encode("ascii")


def assignment_cost(model,hard,soft):
    m=set(model)
    if not all(any(l in m for l in c) for c in hard): return None
    return sum(w for w,c in soft if not any(l in m for l in c))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups",type=int,default=120)
    parser.add_argument("--output",type=Path,default=ROOT)
    args=parser.parse_args(); root=args.output.resolve(); root.mkdir(parents=True,exist_ok=True)
    if args.groups<100: parser.error("Each scenario requires at least 100 independent pair groups")
    catalogue=[]; records=[]; pair_records=[]; seen=set(); seen_formulas=set(); counts=Counter()
    def formula_key(n,h,s):
        return digest(json.dumps([n,sorted(sorted(c) for c in h),sorted((w,sorted(c)) for w,c in s)],separators=(",",":")).encode())
    for sid,family,title,scenario,intervention,hypothesis,equation in SPECS:
        spec=dict(id=sid,family=family,title=title,scenario=scenario,intervention=intervention,
                  rationale=hypothesis,equation=equation,targets=["A","D"] if family=="cnf" else ["B","C"],
                  groups=args.groups,examples=3*args.groups)
        catalogue.append(spec)
        for i in range(args.groups):
            seed=int(digest(f"{SEED}/{sid}/{i}".encode())[:16],16); rng=random.Random(seed)
            for attempt in range(1000):
                n,h,s,ch,cs,p=build(sid,rng,i)
                base=serialize(n,h,s,family); changed=serialize(n,ch,cs,family)
                # Identical serialized mathematical pairs are not counted twice.
                pair_hash=digest(base+b"\n---\n"+changed)
                hh,ss,mapping=transformed(n,ch,cs,rng)
                keys=[formula_key(n,h,s),formula_key(n,ch,cs),formula_key(n,hh,ss)]
                if pair_hash not in seen and len(set(keys))==3 and not seen_formulas.intersection(keys):
                    seen.add(pair_hash); seen_formulas.update(keys); break
            else: raise RuntimeError(f"Cannot obtain unique pair {sid}/{i}")
            group=f"{sid}/{i:04d}"; split="train" if i<args.groups*0.6 else "dev" if i<args.groups*0.8 else "test"
            labels=[]; paths=[]
            for variant,hard,soft in [("control",h,s),("challenge",ch,cs),("disguised",hh,ss)]:
                data=serialize(n,hard,soft,family); rel=f"instances/{family}/{sid}/{i:04d}_{variant}.{family}"
                path=root/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
                truth=evaluate(n,hard,soft); labels.append(truth); paths.append(rel)
                row=dict(id=f"{group}/{variant}",group_id=group,scenario_id=sid,variant=variant,split=split,
                         path=rel,format="dimacs-cnf" if family=="cnf" else "wcnf-old",sha256=digest(data),
                         nvars=n,nclauses=len(hard)+len(soft),hard_clauses=len(hard),soft_clauses=len(soft),
                         total_soft_weight=sum(w for w,_ in soft),seed=seed,parameters=p,truth=truth,
                         scenario=scenario,intervention=intervention,rationale=hypothesis,
                         evidence="construction plus complete exhaustive truth table; no baseline evaluated")
                if variant=="disguised": row["challenge_to_disguised_literal_map"]={str(k):v for k,v in mapping.items()}
                if sid in ("ferromagnetic_barrier","feasible_exchange_barrier") and variant=="challenge":
                    trap=p["trap_core_assignment"]+truth["witness"][p["core_nvars"]:]
                    cost=assignment_cost(trap,hard,soft)
                    neighbors=[]
                    for v in range(1,n+1):
                        neighbor=[-l if abs(l)==v else l for l in trap]
                        neighbors.append(assignment_cost(neighbor,hard,soft))
                    assert cost is not None and cost>truth["optimum"]
                    assert all(c is None or c>=cost for c in neighbors)
                    row["suboptimal_trap"]={"assignment":trap,"cost":cost,"gap":cost-truth["optimum"],
                        "one_flip_costs":neighbors,"core_moves_strictly_worse_or_infeasible":all(c is None or c>cost for c in neighbors[:p["core_nvars"]])}
                records.append(row); counts[family]+=1
            a,b,c=labels
            assert b["status"]==c["status"] and b["model_count"]==c["model_count"]
            if family=="wcnf": assert b["optimum"]==c["optimum"]
            pair_records.append(dict(group_id=group,scenario_id=sid,split=split,paths=paths,
                intervention=intervention,control_status=a["status"],challenge_status=b["status"],
                control_optimum=a.get("optimum"),challenge_optimum=b.get("optimum"),
                control_model_count=a["model_count"],challenge_model_count=b["model_count"],
                optimum_delta=b["optimum"]-a["optimum"] if family=="wcnf" else None,
                control_to_challenge="semantic intervention: recompute answer; do not assume equivalence",
                challenge_to_disguised="bijection of variables and polarities plus clause/literal reordering; exact equivalence under supplied map"))
        print(f"Generated {sid}: {args.groups} groups / {args.groups*3} formulas",flush=True)
    for name,rows in [("manifest.jsonl",records),("pairs.jsonl",pair_records)]:
        (root/name).write_text("".join(json.dumps(r,separators=(",",":"))+"\n" for r in rows),encoding="utf-8")
    dump(root/"scenarios.json",dict(version=VERSION,master_seed=SEED,scenarios=catalogue))
    dump(root/"summary.json",dict(version=VERSION,seed=SEED,scenarios=len(catalogue),groups=len(pair_records),
        instances=len(records),counts=dict(counts),groups_per_scenario=args.groups,
        max_nvars=max(r["nvars"] for r in records),max_weight_sum=max(r["total_soft_weight"] for r in records),
        statuses=dict(Counter(r["truth"]["status"] for r in records)),
        status_cost_or_model_count_changes=sum((p["control_status"],p["control_optimum"],p["control_model_count"])!=(p["challenge_status"],p["challenge_optimum"],p["challenge_model_count"]) for p in pair_records),
        distinct_formulas_ignoring_clause_and_literal_order=len(seen_formulas),
        splits=dict(Counter(r["split"] for r in records)),
        claim="Constructed adversarial hypotheses; baseline attack success has not been measured."))
    lines=["# MATT mathematical scenario catalogue", "", "Each scenario has 120 pair groups by default. Each group contains a control, a semantic challenge, and an equivalent disguised challenge. See README.md for label and evaluation semantics.", ""]
    for spec in catalogue:
        lines += [f"## {spec['id']}: {spec['title']}","",f"- Targets: {', '.join(spec['targets'])}; format: {spec['family']}; groups: {spec['groups']}; formulas: {spec['examples']}.",f"- Scenario: {spec['scenario']}",f"- Intervention: {spec['intervention']}",f"- Rationale: {spec['rationale']}",f"- Mathematical construction: `{spec['equation']}`", ""]
    (root/"scenarios.md").write_text("\n".join(lines),encoding="utf-8")


if __name__=="__main__": main()
