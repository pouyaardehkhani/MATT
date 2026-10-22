# MATT v2 — mathematical adversarial SAT and MaxSAT formulas

MATT tests whether mathematical changes to valid formulas lead to correct answers, and whether equivalent representations lead to consistent answers. It contains **32 scenarios, 120 control/challenge groups per scenario, and 11,520 formula files**. Every group has three files: a control, a semantic challenge, and an equivalent disguised challenge. There are **3,840 groups**, with **5,760 CNF files** for A/D and **5,760 WCNF files** for B/C. The 120 groups per scenario are counted **before** adding the equivalent representation.

These are formula-level adversarial constructions: rare countermodels, sign-sensitive parity constraints, hidden resource bottlenecks, suboptimal local basins, shared repair costs, and semantic triggers. They are hypotheses about possible weaknesses, **not measured attacks against the existing methods**. No A/B/C/D baseline has been run for this release. A correct complete solver should still give the exact answer. A heuristic solver may legitimately return a suboptimal incumbent; that is an optimization gap, not automatically an incorrectness bug.

The previous parser/boundary dataset is preserved in `legacy_v1/`. It is not part of v2's counts or manifests. V2 has no malformed inputs, empty clauses, empty formulas, tautological clauses, duplicated literals, ambiguous hard/soft boundaries, or overflow-sized weights. All variables occur. Hard constraints of every MaxSAT instance are feasible.

## A concrete cost-7 versus cost-9 trap

Open `instances/wcnf/ferromagnetic_barrier/0000_challenge.wcnf`.

Its optimization core has three variables, soft positive unit clauses `(x1)`, `(x2)`, `(x3)` of weight 3, a negative unit `(NOT x1)` of weight 7, and connected equality preferences of weight 17. Equality `xi = xj` is encoded by two soft clauses `(NOT xi OR xj)` and `(xi OR NOT xj)`, each of weight 17. Exactly one is false when the variables differ, so a disagreement costs 17, not 34.

The all-true core costs **7**. The all-false core costs **9**. Any nonuniform core assignment violates an equality edge, costing at least 17, so the global optimum is 7. From all-false, any single core-variable flip incurs an equality penalty greater than its possible unary gain. Thus the cost-9 assignment is a strict local minimum on the optimization core. A disjoint, satisfiable context adds structural variation with no objective cost; its moves may be neutral or infeasible. The full formula still has no improving one-bit move at the supplied trap assignment.

The manifest includes the full trap assignment, its cost, the optimum gap, and the result of flipping every variable. This proves the existence of a misleading basin. It does **not** prove that a particular local-search method will get stuck: weighting, random moves, restarts, and temporary infeasibility may let it escape. The control uses weak couplings; the challenge strengthens them; the disguised file preserves the challenge under a supplied signed variable bijection.

## What the scenarios cover

The complete construction, intervention, equation, and rationale for every scenario are in [scenarios.md](scenarios.md), with machine-readable versions in `scenarios.json`. Each manifest entry repeats its scenario and rationale and includes the particular construction parameters.

| Task | Mathematical probes |
|---|---|
| A: backbone extraction | Rare but genuine countermodels; anchor reversal through correlated variables; free parity modes becoming forced; conditional thresholds; backbone changes after breaking an exchange symmetry. |
| D: symmetry breaking / SAT | Almost exchangeable choices; signed complement symmetries; conditional rather than global exchanges; color and matching obstructions; parity consistency; bridges between components. |
| B: MaxSAT local search | Certified suboptimal one-flip basins; disconnected feasible orientations; coordinated cover and exact-cardinality exchanges; weight-majority reversals; frustrated signed interactions; conjunction-triggered cost changes. |
| C: exact MaxSAT | Overlapping exclusion cores; shared hitting-set repairs; residual weight accounting; hierarchy tradeoffs; component coupling; complete weighted conflict covers; hard constraints opposed by attractive soft rewards. |

CNF is supplied to A and D; WCNF to B and C. These tasks have different output semantics. The dataset does not pretend one formula file can be passed unchanged to all four interfaces. Future methods can use the matching format and labels.

## Paired design and exact labels

For every scenario, files `0000` through `0119` form 120 groups:

1. `*_control`: the reference mathematical problem.
2. `*_challenge`: a deliberate semantic intervention, such as flipping an XOR relation, changing an objective weight, adding a bridge, or enforcing a trigger. Its answer must be recomputed. It may change satisfiability, backbone, optimum, optimum assignment, or landscape. Some interventions preserve the optimum value while changing the formula or landscape; unchanged cost alone is not evidence the intervention did nothing.
3. `*_disguised`: the challenge with a signed permutation of variables and reordered clauses/literals. It has exactly the same mathematical problem under the supplied map. It is a representation-sensitivity probe, not a third independent problem.

Every file has an exact label computed by evaluating **all assignments**. Boolean truth tables are stored temporarily as Python integer bitsets; weighted violated-clause costs are added by binary bit planes. There is no random sampling or unverified analytical label. The implementation is standard-library Python and uses arbitrary-precision integers.

The manifest supplies SAT/UNSAT status, exact feasible model count, full backbone when satisfiable, a satisfying or optimal witness, and, for MaxSAT, optimum violated-soft-weight cost and exact number of optimal assignments. `backbone` on a WCNF row refers to the **hard-feasible set**, not just optimal assignments. UNSAT rows have `backbone: null`; no arbitrary convention for the backbone of an inconsistent formula is imposed. Witnesses include every declared variable.

`verify.py` re-parses the actual saved formulas and recomputes all labels, checks every witness and supplied local trap, and verifies every representation map at the clause-multiset level. With PySAT enabled it also checks every CNF's status and full backbone using MiniSat22 and every WCNF's optimum using RC2 with Glucose3. A separate scalar assignment loop cross-checks the truth-table arithmetic on a small formula from each scenario. See `validation.json` for the checks actually completed, versions, source and manifest hashes, and outcome. These are computational ground-truth checks; no standalone DRAT/LRAT/VeriPB proofs are supplied.

## Files and schema

```text
MATT/
  README.md
  scenarios.md / scenarios.json   32 construction explanations
  manifest.jsonl                 one record per formula, including ground truth
  pairs.jsonl                    one record per group and intervention
  summary.json                   actual counts and ranges
  validation.json                completed audit results
  reproducibility.json           fresh regeneration and byte-identity check
  generate.py                    deterministic construction + exhaustive labeling
  verify.py                      saved-file audit and optional independent oracles
  instances/cnf/<scenario>/      DIMACS CNF formulas
  instances/wcnf/<scenario>/     conventional old-format WCNF formulas
  legacy_v1/                     preserved earlier dataset, excluded from v2
```

`manifest.jsonl` keys include `id`, `group_id`, `scenario_id`, `variant`, `split`, `path` (relative to MATT), `format`, `sha256`, dimensions, `seed`, `parameters`, `scenario`, `intervention`, `rationale`, and `truth`. Disguised rows additionally contain `challenge_to_disguised_literal_map`: if original variable 2 maps to -5, literal +2 maps to -5 and literal -2 maps to +5. Some challenge rows also contain `suboptimal_trap`.

WCNF uses `p wcnf NV NC TOP`, with `TOP = sum(all soft weights) + 1`; hard clause weights equal TOP, and all soft weights are strictly smaller. Cost always means **the sum of weights of violated soft clauses, subject to satisfying every hard clause**. Format conversion, if needed for a particular original executable, must preserve this meaning. The stored data uses one unambiguous dialect; alternate dialect copies are not counted as new examples.

## Reproduce and audit

Use Python 3.10 or newer. Generation and exhaustive checking require no third-party packages. The shipped default has master seed `20261016` and 120 groups per scenario. Generation rejects repeated formulas even after ignoring clause/literal order. It varies core parameters, graph edges, phases, weights, thresholds, circuit topology, and a small disjoint planted satisfiable context. Renaming alone does not produce additional groups. This is not a guarantee of 120 non-isomorphic or statistically independent structural motifs: some small core templates recur, and the manifest makes the core/context distinction explicit.

```powershell
python MATT/generate.py
python MATT/verify.py
# Include independent oracles from the repository's existing PySAT installation:
python MATT/verify.py --pysat-path envs/sat-core/Lib/site-packages
# Or, if PySAT is installed for the active Python:
python MATT/verify.py --pysat
# Reproduce into a separate directory:
python MATT/generate.py --output MATT/reproduced
```

On this machine the old `envs/sat-core/Scripts/python.exe` launcher references a missing Python installation. This release was generated and audited with the bundled Python 3.12 runtime, adding the existing `envs/sat-core/Lib/site-packages` for the optional oracle check. No environment files or baseline code were changed.

Regeneration writes the v2 generated paths; it does not alter `legacy_v1`. If changing group counts or construction code, use a fresh `--output` directory so files from an older larger run cannot be mistaken for current manifest members. The manifest is the authoritative membership list.

The shipped release was also regenerated into a fresh temporary directory. All 11,520 formula hashes and the five generated metadata/catalogue files matched exactly; `reproducibility.json` records that check. Regeneration after editing the generator defines a different dataset version and requires a new audit.

## Later evaluation and scientific limits

Evaluate later using the ground truth rather than comparing methods only with one another. Validate any returned assignment against the **original formula** and recompute its original objective. For B, distinguish no feasible incumbent, feasible cost gap `returned_cost - optimum`, and a wrong feasibility/cost claim. Returning cost 9 with a valid model when OPT=7 is a gap of 2; calling it proven optimal would be a correctness failure. For C, a claimed optimum must equal the exact optimum. For A, compare full backbone sets only for completed runs; a partial timeout result is not a completed wrong backbone.

For D, symmetry breaking deliberately removes symmetric models. The reduced formula need not retain the original model count or backbone. Check satisfiability preservation and validate reconstructed models against the original. A/D labels are for the original input. Claiming that symmetry breaking must preserve every model, or the exact original backbone, would be an invalid test.

The provided 60/20/20 split keeps all three members of each group together. Do not train on one representation and evaluate on another from the same group. This split is for convenience, not a strong novelty guarantee: related templates and isomorphic cores can occur across groups. For scientific generalization claims, also hold out entire scenarios and group structurally related families; deduplicate isomorphic formulas if required by the protocol. Report results by scenario and across multiple solver seeds and budgets. Count groups, not disguised copies, as the principal paired evaluation units.

There are 5–18 variables per file, deliberately small enough for exhaustive ground truth. These are diagnostic constructions, not a stand-alone large-scale runtime benchmark. Pair them with real and larger synthetic benchmarks for performance claims. The 120 groups per scenario exceed the requested minimum but cannot guarantee perfect evaluation or complete robustness. Existing search methods may solve every file; a lack of failures remains a valid result. The trigger analogy concerns formula semantics, not a learned backdoor, poisoned training process, or hidden modification of the baseline methods.
