# MATT extension research

Research date: 16 October 2026. This document records the proposal made before the v3 expansion. Its acquisition-status statements are historical. See [README.md](README.md), `summary.json`, and `validation.json` for the sources actually imported, implemented families, current counts, and completed checks. V2 metadata and its original audit are preserved under `releases/v2/`.

## Assessment of the current data

MATT v2 contains 32 scenarios and 120 groups per scenario, totaling 11,520 files including representation variants. Its strengths are explicit interventions, exhaustive labels, paired controls, and supplied trap assignments. It is a compact diagnostic suite: every formula has 5–18 variables.

The most valuable improvements are larger optimization cores, more distinct mathematical structures, historical counterexamples, and additional transformations with exact answer relations. Increasing the number of renamed copies would not address these gaps. Some current groups share small core templates and obtain additional variation from a disjoint context; a future release should measure diversity of the core itself.

No finite dataset is complete for all SAT/MaxSAT methods. A defensible goal is documented coverage of specified mathematical failure mechanisms, size ranges, source families, and label confidence. A good complete solver can pass all correctness tests. For local search, a feasible suboptimal answer under a finite budget is a quality gap; a falsely claimed optimum or invalid model is a correctness failure.

## Existing resources, prioritized

### 1. MaxSAT Regression Suite — closest ready-made match

[Official repository](https://github.com/tobipaxe/MaxSATRegressionSuite).

This is an existing counterexample collection, with a runner and CSV metadata. Its formulas were obtained by fuzzing and reducing examples that exposed earlier evaluation solvers. The documentation distinguishes a suboptimal result incorrectly labeled optimal from a valid, unfinished incumbent. It also says most reference optima were certified, rather than claiming every label was certified.

Recommended use: curate ordinary, valid formulas associated with incorrect costs, models, or optimality claims. Preserve source instance IDs and documented failure information. Keep boundary-only and crash-only examples outside the main mathematical collection. A historical failure does not establish a defect in any current A/B/C/D version. The runner's anytime mode is partly about interrupted output, so selecting that entire folder would not directly match this project's objective.

The repository documents the archive at [the MSE 2024 site](https://maxsat-evaluations.github.io/2024/MaxSATRegressionSuiteWCNFs.zip). The archive itself was not downloaded or audited in this research step.

### 2. Research behind the regression corpus

[Paxian and Biere, *MaxSAT Fuzzing and Delta Debugging*, JAIR 2026](https://cca.informatik.uni-freiburg.de/papers/PaxianBiere-JAIR26.pdf), especially Sections 4.1 and 4.6.

The paper reports failures including incorrect optimality bounds and a soundness failure, alongside crashes and performance problems. It describes a public minimized regression corpus and identifies its archived artifact by DOI [10.5281/zenodo.15773637](https://doi.org/10.5281/zenodo.15773637). The archive record could not be fetched through the web tool during this check; that identifier is supported by the paper's data-availability statement and references.

Recommended use: use the paper's failure categories to annotate imported examples and distinguish proven optimum, best-known bound, and unresolved disagreement. This is relevant prior work for a paper claiming adversarial robustness evaluation of MaxSAT methods.

### 3. Hidden-optimum weighted Max-2-SAT — larger mathematical challenges

[Ke Xu's official benchmark page](https://rb-bench.github.io/benchmarks/weighted-max2sat.html).

These Model RB-derived instances include hidden optimum solutions and an optimum annotation. The listed small and large groups range from 60 to 1,534 Boolean variables, with five instances per listed size. This is a useful source of larger instances, but not automatically 100 independent examples per scenario.

Important integration detail: this source states the objective as maximized satisfied weight. MATT records minimized violated weight. Convert using `minimum_violated = total_soft_weight - maximum_satisfied`, after verifying the source format and hard/soft interpretation. Retain both objective conventions in provenance. Use the published generator model to obtain additional independently seeded instances; do not count relabelings of the five originals as independent source examples.

### 4. CNFgen, particularly Pitfall formulas — structured heuristic deception

[CNFgen project](https://massimolauria.net/cnfgen/) and [official Pitfall documentation](https://cnfgen.readthedocs.io/en/latest/cnfgen.families.pitfall.html).

Pitfall formulas are explicitly designed to mislead common CDCL decision heuristics toward a difficult subformula despite having an easier resolution route. They are UNSAT formulas, useful as structured search challenges; they are not a guarantee of wrong answers. The family has tunable graph and gadget parameters, so it can generate genuinely different cores.

Other documented families include [pebbling and Stone formulas](https://cnfgen.readthedocs.io/en/latest/cnfgen.families.pebbling.html). Treat generator output as requiring verification and retain the generator version, seed, and parameters.

### 5. MaxSAT Evaluation 2026 — realistic problem scale

[Official benchmark archive and metadata](https://zenodo.org/records/21358014).

The release provides track-specific formula archives and metadata containing family, best-known cost, and optimal cost information. Recommended use: choose a diverse, bounded-size sample of real benchmark families, then construct controlled perturbation pairs. These are general benchmarks, not an already curated adversarial set. A best-known value must not be promoted to a proven optimum when the metadata does not establish optimality.

### 6. SAT Competition / GBD and SATLIB — realistic CNF source formulas

[SAT Competition 2026](https://satcompetition.github.io/2026/) links its tagged competition instances in [GBD](https://benchmark-database.de/?track=main_2026). [SATLIB](https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html) supplies established DIMACS families.

Recommended use: import a stratified selection of structured CNFs as original formulas for controlled transformations. Existing SAT status does not supply a complete backbone label: A requires additional backbone computation or proof of the relevant literals. Keep source versions and problem-family identity so related instances do not leak across train/test splits.

### 7. Neural SAT adversarial robustness — relevant to the attack analogy

[Official ICLR 2022 repository: *Generalization of Neural Combinatorial Solvers Through the Lens of Adversarial Robustness*](https://github.com/johannaSommer/generalization-neural-co-solvers).

This supplies SAT perturbation and attack-generation code aimed at neural combinatorial solvers, including NeuroSAT, with tests for retaining the true label. It is a framework/generator rather than a universal ready-labeled attack corpus for traditional solvers. Recommended use: adapt its perturbation ideas and original-variable mappings, especially if a future method includes learning. Its attacks are model-dependent; success against a neural classifier does not establish failure of an exact solver.

## Recommended new scenario specifications

The following are proposed constructions. Their suitability is an engineering/mathematical assessment, not an empirical claim that an A/B/C/D method fails. Each implemented family should have at least 120 distinct core instances before representation variants, with a scenario description, exact intervention, original-to-modified relation, and explicit label evidence.

| Priority | Proposed scenario | Construction and reason | Required reference evidence |
|---|---|---|---|
| P1 | Tunable multi-flip barriers | Build coupled blocks requiring coordinated changes of 2, 4, 8, or more variables; vary the core graph rather than attaching unrelated context. Separates shallow traps from collective-move difficulty. | Optimum witness and lower bound; an explicit suboptimal assignment; bounds on escape distance and cost barrier for the defined move model. |
| P1 | Entropic traps | Construct many near-optimal assignments competing with a small optimal basin. Separates large basin attraction from simple one-flip steepness. | Exact or construction-proven optimum and basin/model counts; avoid treating an approximate sample count as exact. |
| P1 | Objective-breaking apparent symmetry | Use a symmetric hard-feasible region but asymmetrical soft weights or soft clauses. Exchanging two variables preserves feasibility but changes cost. | A concrete exchange mapping, a feasible assignment, and before/after costs showing that the exchange is not an objective symmetry. This extends the WCNF side; it does not make D's CNF-only interface accept WCNF. |
| P1 | Finite-weight priority thresholds | Place a large weight just below/equal/above the total competing loss using normal integer sizes. Tests whether a method incorrectly treats a finite soft priority as an absolute hard requirement. | Separate exact optimum for each threshold; report assignment changes even when cost ties occur. This should broaden the existing hierarchy scenarios with distinct nested structures. |
| P1 | Large rare-countermodel cores | Construct correlated components with one rare escape branch, then close it using a controlled trigger. Scale the actual correlated core. | SAT witness and countermodel per non-backbone literal, or UNSAT evidence for forced literals; no inference from model sampling alone. |
| P1 | Nested and shared conflict repairs | Generate overlapping resource demands where one relaxation repairs several conflicts and other relaxations repair only one. Add nested rather than only pairwise conflicts. | Optimal witness plus lower-bound proof; annotate distinct conflict sets and overlap. Tests unsupported independent-core cost addition. |
| P2 | Encoding changes with projection maps | Encode the same cardinality/resource problem using different auxiliary encodings, such as sequential and totalizer-style constructions. | Original-variable projection map, equivalence of projected feasible solutions and objectives; auxiliary backbones/model counts need not match. |
| P2 | Redundant implied-constraint amplification | Add logically implied hard clauses selected to distort occurrence counts, graph structure, or heuristic activity while preserving the underlying problem. | Implication proof or exhaustive verification; SAT, original-variable backbone, and MaxSAT optimum unchanged. Arbitrary added soft clauses are not safe. |
| P2 | Soft-weight split invariance | Replace `(C,w)` with several copies `(C,w1)...(C,wr)` where positive integer weights sum to w. | Pointwise equality of the objective for every feasible assignment. Originals and transformed versions belong to the same evaluation group. |
| P2 | Cost scaling and constant offsets | Scale all soft weights by positive integer k. Separately add a fresh soft pair `(z,a)` and `(NOT z,a)` with no other occurrences of z. | Scaling multiplies OPT by k; the contradictory nonempty soft pair adds exactly a to OPT. Annotate fresh-variable freedom rather than expecting identical model counts. |
| P2 | Matched superficial statistics | Pair distinct formulas with matched variable/clause counts, widths, and similar local degree statistics but different global constraints or objective landscapes. | Independently certified answers for both; matched statistics alone do not prove equivalence or different difficulty. Useful for heuristic or learned selector generalization. |
| P2 | General graph parity / Tseitin obstructions | Move beyond cycles to varying-degree connected graphs and controlled charge/parity changes. | Construction-based parity consistency argument plus solver/proof validation; graph isomorphism checks where feasible. |
| P2 | Pitfall and propagation gadgets | Generate Pitfall and pebbling/Stone-style cores using documented generators; vary graph topology and size. | SAT/UNSAT evidence for each formula, retained seeds/versions, and an explanation of the misleading structural mechanism. Performance sensitivity is measured later. |
| P2 | Small structured edits to real formulas | Starting from selected application instances, add certified implied constraints, apply valid encoding transformations, or introduce a semantic edit with a newly established optimum. | Source formula ID, edit budget, certificate status, mapping, and exact label relation; do not assume a changed formula keeps the source's optimum. |

For scale, use a ladder such as 50, 200, 1,000, and 5,000 variables where appropriate. These are target ranges, not an instruction to pad a tiny core with free variables. Generate different graph structures, clause patterns, coupling arrangements, and weight regimes at each applicable scale. Retain a small exactly enumerated counterpart to validate each construction. Large labels need constructions or checked bounds/proofs because full truth tables no longer scale.

## Integration and evaluation design

Keep three explicit origins in the next manifest: constructed scenarios, historical regression counterexamples, and controlled derivatives of real benchmark formulas. Add a fourth tag for verified failures discovered by later method-specific searches. An untested construction must not receive the same evidence label as a historically observed failure.

For each imported original, record source URL/DOI, version or retrieval date, original filename, checksum, family, format, objective convention, source label, certificate availability, known affected solver/version if documented, and redistribution terms. Preserve originals; format conversions belong to mapped derivatives. Filter main-set membership by mathematical content and valid syntax. Do not recreate excluded empty/parser cases just to increase counts.

Use label states such as `exhaustive`, `construction_proved`, `certificate_checked`, `solver_cross_checked`, and `best_known_only`, with a separate field describing exactly which fact was checked. An independently verified feasible model gives an upper bound, not an optimum proof. Do not fill missing optimum or backbone fields with guesses.

A historical suite may have fewer than 100 distinct examples for a particular bug category. Preserve the genuine count. Generate and validate an additional scenario family if needed, but do not rename a small imported set and report 100 independent counterexamples. Deduplicate mathematical cores, not only file bytes, and keep all descendants of an original source in one split. Hold out entire mechanisms or families in addition to the ordinary group split.

Method-targeted generation is valuable later: search under a defined edit budget for a larger MaxSAT cost gap, or minimize a reproducible false SAT/UNSAT/backbone/optimum claim. That phase requires running the target methods. It has not been performed here, consistent with the decision to test the methods later.

Recommended first tranche: curated semantic counterexamples from the regression suite, generated hidden-optimum MaxSAT cores, tunable barriers, objective-asymmetric symmetries, and projection-checked encodings. These additions improve evidence and diversity more directly than increasing representation-copy counts.
