# MATT mathematical scenario catalogue

Each scenario has 120 pair groups by default. Each group contains a control, a semantic challenge, and an equivalent disguised challenge. See README.md for label and evaluation semantics.

## rare_escape: Rare countermodel closed by a trigger

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: A selector s normally agrees with an output x; the opposite branch requires every trigger bit to be true.
- Intervention: Add one clause forbidding the all-true trigger.
- Rationale: Model sampling can confuse a highly biased literal with a backbone. Closing the escape makes it genuinely forced.
- Mathematical construction: `(s OR t_i) for all i, x <-> s; intervention: OR_i NOT t_i.`

## implication_reversal: Reconvergent implication orientation

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: A connected equality network carries a hidden anchor through many paths.
- Intervention: Reverse the anchor polarity while keeping the network.
- Rationale: A cached or partially propagated backbone must change sign throughout the component.
- Mathematical construction: `x_i <-> x_j on a connected graph; (a OR q) AND (a OR NOT q), then a becomes NOT a.`

## parity_cycle: One parity sign changes consistency

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: Pairwise XOR relations close a cycle whose XOR sum is zero.
- Intervention: Flip the parity on the closing edge.
- Rationale: Local consistency of individual clauses does not establish global satisfiability.
- Mathematical construction: `XOR_i (x_i XOR x_(i+1)) = 0; one RHS flip makes it 1.`

## parity_pin: Free parity mode becomes a full backbone

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: A signed equality tree has two complementary solutions.
- Intervention: Pin one variable with a two-clause anchor.
- Rationale: A single semantic intervention forces an entire correlated component.
- Mathematical construction: `x_i XOR x_parent(i) = b_i; add (x_1 OR q) AND (x_1 OR NOT q).`

## cardinality_boundary: Overlapping cardinality contradiction

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: A resource pool requires exactly k active items.
- Intervention: Add an at-least-(k+1) requirement on the same pool.
- Rationale: Different cardinality constraints look individually feasible but jointly contradict one another.
- Mathematical construction: `sum x_i = k versus sum x_i = k AND sum x_i >= k+1.`

## unique_witness_block: Blocking a globally unique witness

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: A signed connected network plus an anchor has exactly one core assignment.
- Intervention: Add one clause falsified by that complete core assignment.
- Rationale: A long added clause can eliminate the last model despite leaving every variable well formed.
- Mathematical construction: `F has unique core model m; F AND (OR_i NOT m_i) has none.`

## broken_exchange: Nearly exchangeable choices

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: Exactly one interchangeable option is chosen.
- Intervention: Forbid one option using a relation to a fresh signal rather than changing the format.
- Rationale: A symmetry assumption from the control becomes invalid; one variable enters the backbone.
- Mathematical construction: `sum x_i = 1; add (NOT x_j OR z) AND (NOT x_j OR NOT z).`

## complement_orientation: Signed symmetry loses one orientation

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: Variables in two classes are equal within a class and opposite across classes.
- Intervention: Add a disjunction containing literals true in only one orientation.
- Rationale: Polarity-aware symmetry and backbone logic must distinguish the two complementary models.
- Mathematical construction: `x_i XOR x_j = phase_i XOR phase_j; add a clause selecting one phase.`

## conditional_exchange: Conditional symmetry is not global symmetry

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: Each choice x_i has its own indicator y_i; options initially exchange together.
- Intervention: Add a cross-condition coupling one option to a different indicator.
- Rationale: Exchanging only the option variables or reusing a former global symmetry can delete valid solutions.
- Mathematical construction: `sum x_i=1, y_i <-> x_i; add NOT x_a OR y_b for a != b.`

## bipartite_frustration: A graph becomes non-bipartite

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: Two-color constraints lie on a connected bipartite graph.
- Intervention: Add an edge within one color class.
- Rationale: One local edge creates a global odd-cycle obstruction.
- Mathematical construction: `For each edge enforce x_u XOR x_v=1; the extra edge closes an odd cycle.`

## hall_deficiency: Hidden resource bottleneck

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: A bipartite assignment graph admits a perfect matching.
- Intervention: Restrict two agents to the same single resource.
- Rationale: Per-agent availability is nonempty but the joint resource allocation is impossible.
- Mathematical construction: `Exactly one edge per agent, at most one per resource; |N({a,b})|=1<2.`

## color_obstruction: Color symmetry with a local obstruction

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: A triangle and an extra vertex admit three colors.
- Intervention: Connect the extra vertex to every triangle vertex.
- Rationale: The same color permutations remain available, but the extra clique makes the formula UNSAT.
- Mathematical construction: `3-color K3 plus v; intervention completes K4, which needs four colors.`

## reconvergent_circuit: Circuit output phase intervention

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: A random acyclic AND/OR/XOR circuit has a planted, fixed input vector and reconvergent paths.
- Intervention: Change the required output from its implied value to its opposite.
- Rationale: Reasoning from local fan-in or an incomplete circuit abstraction can miss the unique output consequence.
- Mathematical construction: `Inputs fixed by two-clause anchors; Tseitin gate equivalences; assert output b versus NOT b.`

## component_bridge: A bridge correlates formerly independent components

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: Two signed connected components each have two orientations.
- Intervention: Add one parity bridge between the components.
- Rationale: Component decomposition must be updated after the intervention; model count halves without necessarily creating a backbone.
- Mathematical construction: `F(X) AND G(Y), then AND (x_1 XOR y_1=b).`

## complete_conflict: Last missing conflict clause

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: All assignments of a small variable block except one are excluded by full-width clauses.
- Intervention: Insert the single omitted conflict clause.
- Rationale: The last globally surviving witness disappears although there is no empty clause or direct contradictory-unit pair.
- Mathematical construction: `All 2^k full-width clauses except C_m versus all 2^k clauses.`

## conditional_threshold: Threshold trigger forces a selector

- Targets: A, D; format: cnf; groups: 120; formulas: 360.
- Scenario: When selector s is false, a pool must have exactly k selected bits; when true the pool is unrestricted.
- Intervention: Raise the guarded lower threshold by one.
- Rationale: Only the trigger branch becomes impossible, creating a selector backbone without making the whole instance UNSAT.
- Mathematical construction: `(s OR CNF(sum x_i<=k)) AND (s OR CNF(sum x_i>=k)); raise lower bound to k+1.`

## ferromagnetic_barrier: Suboptimal one-flip basin with a strict core

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Coupled Boolean choices have a cheap all-true basin and an expensive all-false basin.
- Intervention: Increase equality-coupling weight above the total unary preference weight.
- Rationale: A one-flip improving search can remain at a proven suboptimal feasible assignment; the objective is ordinary integer MaxSAT.
- Mathematical construction: `Soft J*[x_i=x_j], positive units total P, negative anchor B<P. All-true costs B; all-false costs P; J>P+B blocks every core-variable flip.`

## feasible_exchange_barrier: Disconnected feasible orientations

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: A connected hard equality component has two feasible assignments with unequal costs.
- Intervention: Turn soft coupling constraints into hard equalities.
- Rationale: Changing basin requires temporary hard-constraint violations; a feasible incumbent can be suboptimal.
- Mathematical construction: `Hard x_i=x_j; soft positive units total P and negative anchor B<P.`

## weighted_majority: Clause majority disagrees with weight majority

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Many linked positive proxy preferences compete with one negative preference.
- Intervention: Move the negative weight from just below to just above their total.
- Rationale: Choosing the most numerous satisfied clauses gives the wrong weighted optimum after the intervention.
- Mathematical construction: `Hard y_i=x; soft (y_i,1), (NOT x,q); optimum min(m,q), winning orientation reverses at q=m.`

## vertex_cover_star: Coordinated star-cover exchange

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: A star graph can be covered by its center or all leaves, with variable selection costs.
- Intervention: Move center cost across the total leaf cost.
- Rationale: Greedy single-vertex deletion cannot exchange the two covers while staying feasible.
- Mathematical construction: `Hard (c OR l_i); soft NOT c cost W, NOT l_i cost w_i; optimum min(W,sum_i w_i).`

## weighted_parity_frustration: Frustrated weighted cycle

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Weighted parity preferences form a consistent cycle.
- Intervention: Flip the closing parity relation.
- Rationale: The inconsistent cycle must pay at least one edge weight; sacrificing the wrong edge is a measurable cost gap.
- Mathematical construction: `Soft XOR edge relations, same weight for their two CNF clauses; odd parity inconsistency costs the minimum edge weight.`

## overlapping_cores: Shared exclusion cores

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Positive vertex preferences compete under pairwise exclusion constraints.
- Intervention: Add overlapping exclusions around a high-degree vertex.
- Rationale: Counting overlapping conflicts independently can overestimate a lower bound or choose poor relaxations.
- Mathematical construction: `Hard NOT x_u OR NOT x_v; soft (x_v,w_v): optimum = total weights minus maximum-weight independent set.`

## weighted_hitting_set: Shared repair covers many demands

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Each demand is a disjunction of possible repairs, each with an activation cost.
- Intervention: Add one shared repair to several demands.
- Rationale: Repairing each demand independently misses savings from one shared activation.
- Mathematical construction: `Hard OR_{v in S_j} x_v; soft (NOT x_v,w_v): minimum-weight hitting set.`

## capacity_weight_swap: Capacity threshold and close weights

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: At most k rewards can be selected.
- Intervention: Raise a formerly excluded item's weight above a selected item's weight.
- Rationale: A stale ranking or an overaggressive weight bucket keeps a feasible but suboptimal solution.
- Mathematical construction: `Hard sum x_i<=k; soft (x_i,w_i); optimum is sum of the n-k smallest weights.`

## exact_cardinality_exchange: No feasible single-bit move

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Exactly k choices must remain active, with weighted rewards.
- Intervention: Add weak pairwise agreement preferences to change the best exchange.
- Rationale: Every one-bit change violates feasibility; improvement requires a coordinated two-bit exchange or temporary infeasibility.
- Mathematical construction: `Hard sum x_i=k; soft unary rewards plus equality preferences on selected random pairs.`

## residual_weight_reversal: Small residual after competing preferences

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Opposite soft preferences on a hard-linked component mostly cancel.
- Intervention: Change one weight by a small amount across the residual balance point.
- Rationale: Dropping a residual or forgetting a constant cost can reverse the optimum or misreport its value.
- Mathematical construction: `Hard y_i=x; soft (x,a),(NOT x,b),(y_i,c_i); compare b with a+sum c_i.`

## hierarchical_tradeoff: One high priority trades against many lower priorities

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Exactly one of two assignment bundles is feasible.
- Intervention: Change the high-level preference across the total lower-level loss.
- Rationale: Treating finite weights as absolute priorities changes the actual weighted problem.
- Mathematical construction: `Hard bundle equivalences/oppositions; soft lower rewards sum L versus a high preference of weight L-1 or L+1.`

## cost_component_bridge: Coupling breaks objective additivity

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Two independently optimized bundles prefer opposite orientations.
- Intervention: Add one hard equality across the bundles.
- Rationale: The sum of old component optima is no longer achievable after coupling.
- Mathematical construction: `min f(X)+min g(Y) becomes min_{x_1=y_1}(f(X)+g(Y)).`

## last_soft_conflict: A complete weighted conflict cover

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: Full-width soft clauses exclude every core assignment except one.
- Intervention: Insert the omitted soft clause with a positive weight.
- Rationale: The optimum changes from zero to the least clause weight, so a stale zero-cost model is invalid.
- Mathematical construction: `Each full-width clause is false at exactly one assignment; after all 2^k are present OPT=min_C w_C.`

## spin_glass_intervention: Competing signed pair interactions

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: A connected graph mixes weighted equality, inequality, and unary preferences.
- Intervention: Flip the preferred relation on one influential edge.
- Rationale: A local sign change can rearrange the global optimum; local edge satisfaction alone is insufficient.
- Mathematical construction: `Minimize sum_e w_e*[x_u XOR x_v != b_e] plus unary penalties.`

## conjunction_trigger: A conjunction trigger disables the cheap branch

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: A selector controls two feasible cost basins and is linked to a multi-bit trigger.
- Intervention: Require all trigger bits, thereby forcing the more expensive selector orientation.
- Rationale: A semantic trigger changes the feasible optimum rather than the input syntax; cached incumbents must be rechecked.
- Mathematical construction: `t_1 AND ... AND t_k -> s; s=false costs B, s=true costs P>B; add hard t_i=true.`

## hard_priority_lure: Very attractive infeasible assignment

- Targets: B, C; format: wcnf; groups: 120; formulas: 360.
- Scenario: A hard capacity constraint rules out selecting every profitable item.
- Intervention: Add a hard exclusion between two high-reward items.
- Rationale: Soft improvement must never be reported as a feasible solution if it violates even one hard constraint.
- Mathematical construction: `Hard sum x_i<=k plus NOT x_a OR NOT x_b; soft (x_i,w_i). All weights remain small and positive.`
