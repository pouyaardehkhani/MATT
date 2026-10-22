# MATT v3 scenario catalogue

62 scenarios and source collections. Count groups before representation variants. Published originals retain their actual available counts; no copied originals are presented as independent examples.

## rare_escape: Rare countermodel closed by a trigger

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: A selector s normally agrees with an output x; the opposite branch requires every trigger bit to be true.
- Rationale: Model sampling can confuse a highly biased literal with a backbone. Closing the escape makes it genuinely forced.
- Intervention: Add one clause forbidding the all-true trigger.

## implication_reversal: Reconvergent implication orientation

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: A connected equality network carries a hidden anchor through many paths.
- Rationale: A cached or partially propagated backbone must change sign throughout the component.
- Intervention: Reverse the anchor polarity while keeping the network.

## parity_cycle: One parity sign changes consistency

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: Pairwise XOR relations close a cycle whose XOR sum is zero.
- Rationale: Local consistency of individual clauses does not establish global satisfiability.
- Intervention: Flip the parity on the closing edge.

## parity_pin: Free parity mode becomes a full backbone

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: A signed equality tree has two complementary solutions.
- Rationale: A single semantic intervention forces an entire correlated component.
- Intervention: Pin one variable with a two-clause anchor.

## cardinality_boundary: Overlapping cardinality contradiction

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: A resource pool requires exactly k active items.
- Rationale: Different cardinality constraints look individually feasible but jointly contradict one another.
- Intervention: Add an at-least-(k+1) requirement on the same pool.

## unique_witness_block: Blocking a globally unique witness

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: A signed connected network plus an anchor has exactly one core assignment.
- Rationale: A long added clause can eliminate the last model despite leaving every variable well formed.
- Intervention: Add one clause falsified by that complete core assignment.

## broken_exchange: Nearly exchangeable choices

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: Exactly one interchangeable option is chosen.
- Rationale: A symmetry assumption from the control becomes invalid; one variable enters the backbone.
- Intervention: Forbid one option using a relation to a fresh signal rather than changing the format.

## complement_orientation: Signed symmetry loses one orientation

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: Variables in two classes are equal within a class and opposite across classes.
- Rationale: Polarity-aware symmetry and backbone logic must distinguish the two complementary models.
- Intervention: Add a disjunction containing literals true in only one orientation.

## conditional_exchange: Conditional symmetry is not global symmetry

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: Each choice x_i has its own indicator y_i; options initially exchange together.
- Rationale: Exchanging only the option variables or reusing a former global symmetry can delete valid solutions.
- Intervention: Add a cross-condition coupling one option to a different indicator.

## bipartite_frustration: A graph becomes non-bipartite

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: Two-color constraints lie on a connected bipartite graph.
- Rationale: One local edge creates a global odd-cycle obstruction.
- Intervention: Add an edge within one color class.

## hall_deficiency: Hidden resource bottleneck

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: A bipartite assignment graph admits a perfect matching.
- Rationale: Per-agent availability is nonempty but the joint resource allocation is impossible.
- Intervention: Restrict two agents to the same single resource.

## color_obstruction: Color symmetry with a local obstruction

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: A triangle and an extra vertex admit three colors.
- Rationale: The same color permutations remain available, but the extra clique makes the formula UNSAT.
- Intervention: Connect the extra vertex to every triangle vertex.

## reconvergent_circuit: Circuit output phase intervention

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: A random acyclic AND/OR/XOR circuit has a planted, fixed input vector and reconvergent paths.
- Rationale: Reasoning from local fan-in or an incomplete circuit abstraction can miss the unique output consequence.
- Intervention: Change the required output from its implied value to its opposite.

## component_bridge: A bridge correlates formerly independent components

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: Two signed connected components each have two orientations.
- Rationale: Component decomposition must be updated after the intervention; model count halves without necessarily creating a backbone.
- Intervention: Add one parity bridge between the components.

## complete_conflict: Last missing conflict clause

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: All assignments of a small variable block except one are excluded by full-width clauses.
- Rationale: The last globally surviving witness disappears although there is no empty clause or direct contradictory-unit pair.
- Intervention: Insert the single omitted conflict clause.

## conditional_threshold: Threshold trigger forces a selector

- Origin: constructed_v2; format: cnf; groups: 120; records: 360.
- Scenario: When selector s is false, a pool must have exactly k selected bits; when true the pool is unrestricted.
- Rationale: Only the trigger branch becomes impossible, creating a selector backbone without making the whole instance UNSAT.
- Intervention: Raise the guarded lower threshold by one.

## ferromagnetic_barrier: Suboptimal one-flip basin with a strict core

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Coupled Boolean choices have a cheap all-true basin and an expensive all-false basin.
- Rationale: A one-flip improving search can remain at a proven suboptimal feasible assignment; the objective is ordinary integer MaxSAT.
- Intervention: Increase equality-coupling weight above the total unary preference weight.

## feasible_exchange_barrier: Disconnected feasible orientations

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: A connected hard equality component has two feasible assignments with unequal costs.
- Rationale: Changing basin requires temporary hard-constraint violations; a feasible incumbent can be suboptimal.
- Intervention: Turn soft coupling constraints into hard equalities.

## weighted_majority: Clause majority disagrees with weight majority

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Many linked positive proxy preferences compete with one negative preference.
- Rationale: Choosing the most numerous satisfied clauses gives the wrong weighted optimum after the intervention.
- Intervention: Move the negative weight from just below to just above their total.

## vertex_cover_star: Coordinated star-cover exchange

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: A star graph can be covered by its center or all leaves, with variable selection costs.
- Rationale: Greedy single-vertex deletion cannot exchange the two covers while staying feasible.
- Intervention: Move center cost across the total leaf cost.

## weighted_parity_frustration: Frustrated weighted cycle

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Weighted parity preferences form a consistent cycle.
- Rationale: The inconsistent cycle must pay at least one edge weight; sacrificing the wrong edge is a measurable cost gap.
- Intervention: Flip the closing parity relation.

## overlapping_cores: Shared exclusion cores

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Positive vertex preferences compete under pairwise exclusion constraints.
- Rationale: Counting overlapping conflicts independently can overestimate a lower bound or choose poor relaxations.
- Intervention: Add overlapping exclusions around a high-degree vertex.

## weighted_hitting_set: Shared repair covers many demands

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Each demand is a disjunction of possible repairs, each with an activation cost.
- Rationale: Repairing each demand independently misses savings from one shared activation.
- Intervention: Add one shared repair to several demands.

## capacity_weight_swap: Capacity threshold and close weights

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: At most k rewards can be selected.
- Rationale: A stale ranking or an overaggressive weight bucket keeps a feasible but suboptimal solution.
- Intervention: Raise a formerly excluded item's weight above a selected item's weight.

## exact_cardinality_exchange: No feasible single-bit move

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Exactly k choices must remain active, with weighted rewards.
- Rationale: Every one-bit change violates feasibility; improvement requires a coordinated two-bit exchange or temporary infeasibility.
- Intervention: Add weak pairwise agreement preferences to change the best exchange.

## residual_weight_reversal: Small residual after competing preferences

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Opposite soft preferences on a hard-linked component mostly cancel.
- Rationale: Dropping a residual or forgetting a constant cost can reverse the optimum or misreport its value.
- Intervention: Change one weight by a small amount across the residual balance point.

## hierarchical_tradeoff: One high priority trades against many lower priorities

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Exactly one of two assignment bundles is feasible.
- Rationale: Treating finite weights as absolute priorities changes the actual weighted problem.
- Intervention: Change the high-level preference across the total lower-level loss.

## cost_component_bridge: Coupling breaks objective additivity

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Two independently optimized bundles prefer opposite orientations.
- Rationale: The sum of old component optima is no longer achievable after coupling.
- Intervention: Add one hard equality across the bundles.

## last_soft_conflict: A complete weighted conflict cover

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: Full-width soft clauses exclude every core assignment except one.
- Rationale: The optimum changes from zero to the least clause weight, so a stale zero-cost model is invalid.
- Intervention: Insert the omitted soft clause with a positive weight.

## spin_glass_intervention: Competing signed pair interactions

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: A connected graph mixes weighted equality, inequality, and unary preferences.
- Rationale: A local sign change can rearrange the global optimum; local edge satisfaction alone is insufficient.
- Intervention: Flip the preferred relation on one influential edge.

## conjunction_trigger: A conjunction trigger disables the cheap branch

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: A selector controls two feasible cost basins and is linked to a multi-bit trigger.
- Rationale: A semantic trigger changes the feasible optimum rather than the input syntax; cached incumbents must be rechecked.
- Intervention: Require all trigger bits, thereby forcing the more expensive selector orientation.

## hard_priority_lure: Very attractive infeasible assignment

- Origin: constructed_v2; format: wcnf; groups: 120; records: 360.
- Scenario: A hard capacity constraint rules out selecting every profitable item.
- Rationale: Soft improvement must never be reported as a feasible solution if it violates even one hard constraint.
- Intervention: Add a hard exclusion between two high-reward items.

## scaled_collective_barrier: Collective barriers from 50 to 5000 variables

- Origin: constructed; format: wcnf; groups: 120; records: 240.
- Scenario: A connected weighted equality network has two uniform basins with different costs.
- Rationale: Every nonuniform assignment pays a coupling larger than the entire unary objective. The only assignment better than the supplied trap differs in every core bit.
- Intervention: Replace uncoupled preferences by strong connected couplings.

## entropic_selector_basin: A rare optimum competes with exponentially many near optima

- Origin: constructed; format: wcnf; groups: 120; records: 240.
- Scenario: A gate permits all trigger bits freely in the expensive branch but requires all of them in the cheap branch.
- Rationale: The objective minimum is unchanged while the proportion of optimal feasible assignments becomes 1/(2^k+1).
- Intervention: Add the multi-bit feasibility trigger.

## objective_asymmetric_symmetry: Feasibility symmetry is not objective symmetry

- Origin: constructed; format: wcnf; groups: 120; records: 240.
- Scenario: Exactly one option is selected from interchangeable hard-feasible choices.
- Rationale: Unequal selection costs destroy objective symmetries despite preserving every hard-feasible exchange.
- Intervention: Change uniform selection costs to distinct costs.

## cardinality_projection_encoding: Different auxiliary encodings of the same choices

- Origin: constructed; format: cnf; groups: 120; records: 240.
- Scenario: An exactly-k selection constraint is encoded with sequential counters and a totalizer.
- Rationale: Answers must agree after projection to primary variables; auxiliary backbones and extension multiplicities need not agree.
- Intervention: Replace the complete auxiliary encoding; retain primary constraints and variable map.

## implied_constraint_amplification: Implied constraints reshape a correlated formula

- Origin: constructed; format: cnf; groups: 120; records: 240.
- Scenario: Two signed connected components contain one anchored orientation and one free orientation.
- Rationale: Adding implied equalities changes occurrence counts and syntactic graph structure without changing any model.
- Intervention: Add many transitive signed equalities.

## soft_weight_partition: Partitioning a clause weight preserves every assignment cost

- Origin: constructed; format: wcnf; groups: 120; records: 240.
- Scenario: A weighted tree-cover objective is represented with one clause per preference.
- Rationale: Replacing a weight by positive summands must preserve the objective pointwise.
- Intervention: Split each positive weight into smaller copies.

## objective_integer_scaling: Exact integer objective scaling

- Origin: constructed; format: wcnf; groups: 120; records: 240.
- Scenario: A weighted tree-cover instance has an optimum calculated by dynamic programming.
- Rationale: Multiplying every soft weight by k must multiply its optimum by k and preserve optimal assignments.
- Intervention: Scale every soft weight by a positive integer.

## nonempty_constant_offset: A provable constant objective offset

- Origin: constructed; format: wcnf; groups: 120; records: 240.
- Scenario: A tree-cover problem gains a fresh soft contradictory pair with equal weights.
- Rationale: Exactly one member of the nonempty fresh-variable pair is false, adding a constant for every feasible assignment.
- Intervention: Add (z,a) and (NOT z,a) on a fresh variable.

## general_graph_tseitin: Matched local statistics, different global parity

- Origin: constructed; format: cnf; groups: 120; records: 240.
- Scenario: Edge variables satisfy parity charges on a connected bridgeless regular graph.
- Rationale: Flipping one vertex charge changes consistency while preserving the factor graph, clause widths, and literal counts per local parity constraint.
- Intervention: Flip one vertex charge, keeping all other data fixed.

## cnfgen_pebbling: Propagation across reconvergent directed graphs

- Origin: external_generator; format: cnf; groups: 120; records: 240.
- Scenario: A unique-sink DAG propagates source truth toward a forbidden sink.
- Rationale: Many paths share consequences; the sink contradiction is global in the graph construction.
- Intervention: Add the original generator's sink-false clause.

## cnfgen_stone: Stone-color propagation conflicts

- Origin: external_generator; format: cnf; groups: 120; records: 120.
- Scenario: Stones on graph sources are red and inherit redness, while sink stones must be blue.
- Rationale: The interaction of stone assignments and propagation adds a distinct structured obstruction.
- Intervention: Vary the DAG, number of stones, and associated assignments.

## cnfgen_subset_cardinality: Locally feasible cardinalities, globally impossible totals

- Origin: external_generator; format: cnf; groups: 120; records: 120.
- Scenario: A 3-regular bipartite incidence graph requires at least two incident selected edges at each left vertex and at most one at each right vertex.
- Rationale: Summing the left requirements exceeds the right capacity although each local constraint is satisfiable.
- Intervention: Vary the bipartite graph while retaining the inconsistent total.

## model_rb_hidden_optimum: Generated Model RB hidden-optimum cores

- Origin: adapted_generator; format: wcnf; groups: 120; records: 240.
- Scenario: One planted choice per variable group avoids all forbidden pairs.
- Rationale: Heavy pair penalties make every optimum respect at-most-one choices; the supplied planted assignment attains the lower bound.
- Intervention: Add cross-group forbidden pairs that keep the planted optimum.

## neural_sat_witness_perturbation: Witness-preserving SAT perturbations

- Origin: adapted_generator; format: cnf; groups: 120; records: 240.
- Scenario: Random clauses are added until the next clause first destroys satisfiability; the satisfiable prefix is retained.
- Rationale: Additional clauses satisfied by a known witness retain SAT while altering structural features.
- Intervention: Add witness-compatible clauses.

## neural_unsat_literal_deletion: UNSAT survives strengthening by literal deletion

- Origin: adapted_generator; format: cnf; groups: 120; records: 240.
- Scenario: A first-conflict random formula is UNSAT.
- Rationale: Deleting literals from nonunit clauses strengthens the formula and therefore preserves UNSAT.
- Intervention: Delete selected literals without creating empty clauses.

## neural_unsat_clause_addition: UNSAT survives added constraints

- Origin: adapted_generator; format: cnf; groups: 120; records: 240.
- Scenario: A first-conflict random formula is UNSAT.
- Rationale: Adding well-formed nonempty clauses preserves the UNSAT label while changing local statistics.
- Intervention: Add extra random nonempty clauses.

## laminar_shared_repairs: Nested repair demands share an ancestor choice

- Origin: constructed; format: wcnf; groups: 120; records: 240.
- Scenario: Each leaf demand may be repaired by selecting any ancestor on its root-to-leaf path.
- Rationale: A single ancestor repairs many nested demands; independent per-demand cost addition can be invalid.
- Intervention: Change the cost of an internal shared repair.

## cnfgen_pitfall: Pitfall formulas with checked signed edge mapping

- Origin: adapted_generator; format: cnf; groups: 120; records: 120.
- Scenario: Pitfall formulas contain easy and hard parts plus a gadget directing common heuristics to the hard part.
- Rationale: A structured heuristic-deception family broadens MATT beyond small planted motifs. The adapter corrects an upstream signed-offset error, documented with preserved originals.
- Intervention: Independent seeds and graph/gadget parameters.

## public_maxsat_regressions: Curated historical MaxSAT regression formulas

- Origin: historical_regression; format: wcnf; groups: 306; records: 306.
- Scenario: A published minimized formula previously exposed a solver issue. The supplied metadata does not identify the precise root cause for every instance.
- Rationale: Independent optimum checking can detect invalid cost or optimality claims on valid, nontrivial formulas. A historical issue is not a demonstrated failure of a current baseline.
- Intervention: 

## public_hidden_optimum_max2sat: Published hidden-optimum Max-2-SAT with independent supplements

- Origin: public_benchmark; format: wcnf; groups: 120; records: 120.
- Scenario: 60 published Model RB hidden-optimum originals plus 60 new independently seeded cores using the same mathematical model.
- Rationale: Provides 120 independent examples of the scenario while preserving the distinction between original published inputs and generated supplements.
- Intervention: 

## satlib_cbs_k3_n100_m403_b10: SATLIB CBS_k3_n100_m403_b10

- Origin: public_benchmark; format: cnf; groups: 120; records: 120.
- Scenario: An established random or controlled-backbone CNF benchmark family from SATLIB.
- Rationale: Adds nontrivial source cores for satisfiability/backbone evaluation; the source family name is preserved and full backbone labels are computed locally.
- Intervention: 

## satlib_cbs_k3_n100_m403_b90: SATLIB CBS_k3_n100_m403_b90

- Origin: public_benchmark; format: cnf; groups: 120; records: 120.
- Scenario: An established random or controlled-backbone CNF benchmark family from SATLIB.
- Rationale: Adds nontrivial source cores for satisfiability/backbone evaluation; the source family name is preserved and full backbone labels are computed locally.
- Intervention: 

## satlib_uf100-430: SATLIB uf100-430

- Origin: public_benchmark; format: cnf; groups: 120; records: 120.
- Scenario: An established random or controlled-backbone CNF benchmark family from SATLIB.
- Rationale: Adds nontrivial source cores for satisfiability/backbone evaluation; the source family name is preserved and full backbone labels are computed locally.
- Intervention: 

## satlib_uf50-218: SATLIB uf50-218

- Origin: public_benchmark; format: cnf; groups: 120; records: 120.
- Scenario: An established random or controlled-backbone CNF benchmark family from SATLIB.
- Rationale: Adds nontrivial source cores for satisfiability/backbone evaluation; the source family name is preserved and full backbone labels are computed locally.
- Intervention: 

## satlib_uuf100-430: SATLIB uuf100-430

- Origin: public_benchmark; format: cnf; groups: 120; records: 120.
- Scenario: An established random or controlled-backbone CNF benchmark family from SATLIB.
- Rationale: Adds nontrivial source cores for satisfiability/backbone evaluation; the source family name is preserved and full backbone labels are computed locally.
- Intervention: 

## satlib_uuf50-218: SATLIB uuf50-218

- Origin: public_benchmark; format: cnf; groups: 120; records: 120.
- Scenario: An established random or controlled-backbone CNF benchmark family from SATLIB.
- Rationale: Adds nontrivial source cores for satisfiability/backbone evaluation; the source family name is preserved and full backbone labels are computed locally.
- Intervention: 

## mse2026_application_selection: Diverse MSE 2026 application instances

- Origin: public_benchmark; format: wcnf; groups: 134; records: 134.
- Scenario: A stratified selection of smaller formulas from weighted and unweighted MSE 2026 archives, covering distinct application families.
- Rationale: Provides real optimization structure and larger scale. Competition reference optima and best-known bounds are retained separately.
- Intervention: 

## satcompetition_archive_selection: SAT Competition archive originals, including 2026 selections

- Origin: public_benchmark; format: cnf; groups: 120; records: 120.
- Scenario: Actual competition CNFs selected from the official 2002â€“2024 archive; matching GBD hashes identify those also selected in the 2026 main track.
- Rationale: Adds established application and crafted structure at realistic sizes. Unknown status and missing backbone labels are explicit; the 2026 file endpoint timed out, so identical identities were retrieved from the official archive.
- Intervention: 

## application_resolution_amplification: Resolution-implied additions to imported CNFs

- Origin: controlled_derivative; format: cnf; groups: 120; records: 240.
- Scenario: A genuine SATLIB benchmark gains clauses obtained by one-step resolution of existing clauses.
- Rationale: The added constraints can change heuristic features but preserve every model and the complete original backbone. Each addition carries its two parent indices and pivot.
- Intervention: Append checked non-tautological resolvents.

## application_objective_scaling: Exact objective scaling on real MaxSAT applications

- Origin: controlled_derivative; format: wcnf; groups: 120; records: 240.
- Scenario: An imported MSE 2026 application formula is reweighted by a positive integer factor.
- Rationale: Every feasible assignment cost scales exactly, giving a checkable relation on real problem structure. Source-only absolute optimum claims remain source-only.
- Intervention: Multiply all soft weights while retaining every hard constraint.
