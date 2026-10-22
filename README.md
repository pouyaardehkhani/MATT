# MATT — mathematical adversarial SAT/MaxSAT evaluation data

**MATT v3** is an evaluation dataset of CNF and WCNF formulas built to test whether SAT and MaxSAT tools stay correct
and robust on inputs designed to mislead them: optimization traps, misleading heuristics, false backbone inferences
and broken symmetry assumptions. Every formula comes with a documented scenario, a paired intervention or an
equivalent disguised form, and a label (SAT/UNSAT, backbone, model count or MaxSAT optimum) with its evidence level.

Author: **Pouya Ardehkhani**

> **The formula files are not in this repository.** Download `MATT-v3-data.zip` (see
> [Getting the data](#getting-the-data)) and unzip it into the repository root. Everything else needed to read,
> verify and regenerate the dataset is here.

Release date: 16 October 2026. MATT now contains **17,360 formula records**, **17,104 distinct formula byte sequences**, **7,640 evaluation groups**, and **62 explained scenarios/source collections**. The combined formats are **8,880 CNFs** and **8,480 WCNFs**. Formula size ranges from **3 to 321,140 declared variables**. New constructed cores reach **5,006 variables**, with no disjoint filler added to inflate that size.

This release combines mathematical constructions, historical counterexamples, established benchmarks, and controlled derivatives of real formulas. The aim is broad, documented coverage of ways valid formulas can mislead optimization, heuristic selection, backbone inference, or symmetry assumptions. No finite dataset is complete for all possible methods or inputs. The formulas target four tasks: backbone extraction (A), anytime MaxSAT (B), exact MaxSAT (C) and SAT symmetry breaking (D); these letters appear in the `targets` field of `scenarios.json`. No performance experiments or method-targeted attack searches are part of this release; independent oracles are used only to establish/check labels.

Current audit: **PASS**. **16,700 records have locally established labels**; **660 remain separate source-reference or unresolved cases**. Exact formula bytes and originals were checked, and the generated extensions were reproduced in a fresh directory.

## Getting the data

The formulas and the derived views are distributed as one archive:

| | |
|---|---|
| File | `MATT-v3-data.zip` |
| Download | **[Google Drive — link to be added](https://drive.google.com/file/d/1g6YCHDQ0jTEUBYbM-lj7f7tbqlV3KaFa/view?usp=sharing)** |
| SHA-256 | `<SHA256_TO_BE_ADDED>` |
| Contents | `instances/` (8,880 CNF + 8,480 WCNF files), `views/` (task and label-confidence subsets), `releases/v3-base-audit/manifest.jsonl` |

```bash
git clone https://github.com/pouyaardehkhani/MATT.git
cd MATT
# download MATT-v3-data.zip into this folder, then:
unzip MATT-v3-data.zip          # creates instances/, views/ and releases/v3-base-audit/manifest.jsonl
python tools/verify_all.py      # checks every manifest path, hash and label certificate
```

Every path in `manifest.jsonl` is relative to the repository root, so the unzipped files are found without
configuration.

## What is in this repository

| In git | In `MATT-v3-data.zip` | Not distributed |
|---|---|---|
| `manifest.jsonl`, `pairs.jsonl`, `scenarios.md/json`, `summary.json`, `validation.json`, `integrity.json`, reproducibility and generator reports, `parts/`, `releases/v2/`, `tools/`, `generate.py`, `verify.py`, `vendor/cnfgen/` (CNFgen 0.9.6 with its license), `sources/*.json` and `sources/INDEX.md` (provenance, selections, exclusions) | `instances/`, `views/`, `releases/v3-base-audit/manifest.jsonl` | `sources/archives/`, `sources/originals/`, `sources/code/` (third-party downloads, kept under their own terms; re-fetch with `tools/download_sources.py`), `legacy_v1/` (the earlier v1 dataset, not part of v3) |

## What was added

| Component | Formula records | Purpose |
|---|---:|---|
| Original v2: 32 scenarios, 120 groups each | 11,520 | Small formulas with exhaustive status, backbone, model-count and optimum labels; paired semantic interventions and equivalent disguised forms. |
| 18 new mathematical families, 120 core groups each | 3,960 | Collective-move barriers, entropic basins, objective-asymmetric symmetries, nested repairs, projection-safe encodings, implied-constraint amplification, exact weight relations, graph parity, CNFgen families, generated hidden-optimum cores, and neural-SAT-inspired perturbations. |
| Curated MaxSAT historical regressions | 306 | Valid positive-cost formulas selected from the public regression archive, excluding boundary-only, trivial, extreme-weight and inconsistent-witness entries. |
| Published hidden-optimum weighted Max-2-SAT | 60 | All 60 published originals, preserved with objective-convention conversion and structural lower-bound checks. |
| Additional hidden-optimum supplements | 60 | New seeded cores supplement the published collection so this mathematical scenario also has 120 groups. These are explicitly generated, not downloaded originals. |
| Six SATLIB families | 720 | Random SAT/UNSAT and controlled-backbone cases: 120 original formulas from each family. |
| MSE 2026 application selection | 134 | A bounded, diverse selection from actual weighted/unweighted competition archives, with source reference costs. |
| SAT Competition archive selection | 120 | Actual official-archive originals, including hash-matched instances also selected for the 2026 main track. |
| Controlled real-formula derivatives | 480 | 120 resolution-amplification pairs and 120 objective-scaling pairs, with explicit mathematical relations. |

Every catalogue scenario/source collection has **at least 120 groups before variants**. The hidden-optimum scenario combines its 60 genuinely published originals with 60 new independently seeded mathematical cores. Origins remain explicit; the supplements are never presented as additional downloaded originals. The separate `model_rb_hidden_optimum` family also supplies 120 generated paired groups. Renaming existing files is never used to manufacture missing originals.

There are 256 duplicate formula records, mostly explicit controls reused in real-formula pairs and some shared controls within mathematical families. `duplicate_formula_of` identifies these, and source/duplicate lineage components stay in one split. Counts above are records, not a claim that every record is a mathematically different problem. Variable isomorphism deduplication has not been claimed. The 3,840 v2 disguised copies are equivalent variants within their original groups, not additional independent attacks.

## Mathematical traps and explanations

[scenarios.md](scenarios.md) explains every scenario and source collection. `scenarios.json` gives the machine-readable catalogue. Every manifest entry includes its scenario, rationale, intervention, instance-specific parameters, origin, tier, and label evidence.

The retained example `instances/wcnf/ferromagnetic_barrier/0000_challenge.wcnf` has optimum **7**, while its supplied feasible cost-**9** assignment has no improving one-variable move. The manifest supplies its complete assignment and neighbor costs. The new `scaled_collective_barrier` family generalizes this mechanism: a connected coupling penalty exceeds the whole unary objective, so every nonuniform assignment costs more than the all-false trap; the cheaper all-true assignment differs in every core bit. Core sizes extend to roughly 5,000 variables.

`entropic_selector_basin` gives the cheap branch exactly one trigger configuration while the expensive branch has exponentially many. `objective_asymmetric_symmetry` preserves exchanges in the hard-feasible region while breaking their objective symmetry. `laminar_shared_repairs` uses exact tree dynamic programming to show how one shared ancestor can satisfy many demands. These are hypotheses about susceptibility, with known mathematical answers; they do not establish that a particular baseline fails.

`cardinality_projection_encoding` changes the complete auxiliary encoding. Its labels explicitly refer to primary variables, and the audit enumerates every primary assignment to verify projection equivalence. Auxiliary backbones and extension counts need not agree. `general_graph_tseitin` keeps the local factor-graph structure while flipping global parity consistency. `application_resolution_amplification` supplies the two parent clauses and pivot for every implied addition to a real imported formula.

The generator audit found a signed-edge-offset error in the upstream Pitfall implementation: some outputs were SAT despite the documented UNSAT construction. MATT preserves the unadapted outputs and upstream code, applies a documented correction only in its adapter, and independently checked the statuses of all 600 CNFgen-family formula records. See `generator-validation.json` and `sources/generator-corrections.json`, including a satisfying witness for an unadapted counterexample. The evaluated Pitfall formulas use the corrected mapping; they are not represented as byte-identical upstream outputs.

## Files and membership

```text
MATT/
  README.md
  manifest.jsonl           authoritative combined membership, labels and provenance
  pairs.jsonl              groups, related members and answer relations
  scenarios.md/json        explanations and construction/source metadata
  summary.json            actual counts, sizes, origins and status categories
  validation.json         completed v3 audit and limits of its checks
  reproducibility-v3.json  fresh generated-formula reproduction check
  instances/cnf/...       normalized DIMACS CNFs for A/D            (data zip)
  instances/wcnf/...      normalized old-format WCNFs for B/C       (data zip)
  views/...               task/label-confidence subsets; no extra formula copies (data zip)
  sources/archives/...    exact fetched archives and metadata, checksummed (not distributed; re-fetch)
  sources/originals/...   preserved original imported formula bytes (not distributed; re-fetch)
  sources/exclusions.json source filtering decisions, with reasons
  sources/duplicate-formulas.jsonl
  parts/...               reproducible component manifests
  tools/...               fetch, curate, generate, assemble and verify programs
  vendor/cnfgen/...       exact CNFgen 0.9.6 generator code used, with its license
  releases/v2/...         preserved v2 metadata, documentation, scripts and audit
```

Only paths listed in `manifest.jsonl` are evaluation members. Source archives, generator code, old releases, and `legacy_v1` are not extra examples. Paths in JSON are relative to MATT. All normalized WCNFs use `TOP = sum(soft weights)+1`; hard weights equal TOP. We minimize violated soft weight subject to all hard clauses. Original source bytes and dialects remain available separately.

The source archive selections are curated subsets, not the entire internet collections. MSE downloads use byte ranges to retrieve selected ZIP members instead of downloading multi-gigabyte archives. The 2026 GBD instance endpoint timed out during acquisition; official SAT Competition archive copies were used instead, with the published GBD identity map. Their metadata states exactly which copies were also in the 2026 selection. The selection and source URLs are retained under `sources/`.

## Label meanings and safe evaluation

Read `truth`, `label_evidence`, and the supplied scope together:

- `OPTIMUM`: the expected violated-weight optimum established locally by exhaustive evaluation, an attaining witness plus a checked structural lower bound, or a construction certificate.
- `OPTIMUM_REFERENCE`: a source-reported optimum. Any source certification claim is preserved; it is not represented as a locally rechecked certificate.
- `FEASIBLE`: a checked feasible assignment and cost without a locally established optimum. `best_known_cost` is not promoted to `optimum`.
- `REFERENCE_ONLY` / `UNKNOWN`: insufficient evidence for a locally established absolute answer. These formulas still support applicable exact transformation relations.
- `SAT` / `UNSAT`: check evidence to distinguish a locally established answer from a GBD source result. Missing backbone fields are not empty backbones.

Backbones refer to all satisfying assignments of a CNF or all hard-feasible assignments of a WCNF, not only optimum assignments. `backbone_complete` states completeness; v2 rows store this outside `truth`, and newer rows inside `truth`. A partial list is not a complete backbone label. Encoding-pair rows use `backbone_scope: primary_variables_only` and list the primary variables.

After the audit, `views/locally-established-labels.jsonl`, `views/maxsat-optimum-local.jsonl`, and `views/sat-status-local.jsonl` select locally established absolute answers. `views/reference-only.jsonl` keeps the remaining rows. `views/complete-backbones.jsonl` selects complete full-variable backbone labels; projection-scoped labels are excluded from that view. Use `views/cnf.jsonl`, `views/wcnf.jsonl`, and `views/large-instances.jsonl` to select formats and size ranges. Views contain metadata references, not additional examples.

A feasibility witness proves an upper bound, not optimality by itself. A group lower bound without a matching witness does not locally prove an imported hidden optimum. Large formulas cannot be exhaustively enumerated; checked graph/weight/tree certificates and explicit source-confidence categories replace that assumption. `validation.json` reports what actually passed, including independently unresolved budget-limited calls. No standalone DRAT/LRAT/VeriPB proof collection is claimed.

The public hidden-optimum source maximizes satisfied weight. Its annotations are converted using `min_violated = total_soft_weight - max_satisfied`. One published file has an inconsistent clause count and an obsolete optimum annotation. Its original is preserved; the normalized count is repaired, and its replacement reference cost is used only when the structural lower bound and an attaining witness establish it. The manifest records both the discrepancy and the evidence. Other filtered or unsupported entries have explicit exclusion records.

## Reproduce or audit

Use Python 3.12 with `python-sat` 1.9.dev15, NetworkX 3.7, and CNFgen 0.9.6, the versions used here (`pip install -r requirements.txt`). The CNFgen code is vendored under `vendor/`. Rebuilding the imported components needs the third-party source archives: run `python tools/download_sources.py` first.

```powershell
# Audit the actual assembled files and supplied mathematical certificates:
python tools/verify_all.py
# Recreate the extra generated families (core files are deterministic):
python tools/build_extensions.py
# Rebuild component imports using retained source archives:
python tools/import_public.py
python tools/import_sat_archive.py
python tools/build_application_pairs.py
python tools/build_rb_supplement.py
# Combine component metadata and regenerate evaluation views:
python tools/assemble.py
python tools/verify_all.py
python tools/check_reproducibility.py
```

The old `generate.py` is retained for reproducing **v2 into a separate output directory**; its default cannot overwrite a v3 release. The original v2 audit and byte-identical reproduction result are preserved under `releases/v2`. The v3 reproducibility report concerns newly generated formulas, not a promise of byte-identical wall-clock-budget-dependent source-oracle metadata. Versioned source archives and original bytes allow imports to be repeated offline. Keep `parts/` until component reconstruction is complete.

## Scientific protocol

Validate returned models and costs against the original input. For B, report feasible cost gaps and success across multiple seeds and budgets; a valid suboptimal incumbent is not automatically a correctness bug. For C, a claimed optimum must equal the applicable proven/reference optimum, with evidence level reported. For A, compare complete backbone sets only after completed extraction, on the specified variable scope. For D, symmetry breaking may remove symmetric models; check SAT preservation and reconstructed model validity rather than requiring the original model count or backbone to remain unchanged.

All members of a source/duplicate lineage stay together in the supplied split. This still does not establish out-of-family independence: hold out entire mechanisms, generator families, and source application families for generalization claims. Count original groups and lineage components, not representation copies, as evaluation units. Small diagnostic formulas and large application problems serve different purposes; report results by scenario and tier rather than allowing a large source collection to dominate one aggregate score.

## Sources and attribution

- [MaxSAT Regression Suite](https://github.com/tobipaxe/MaxSATRegressionSuite), with the [public archive](https://maxsat-evaluations.github.io/2024/MaxSATRegressionSuiteWCNFs.zip).
- Paxian and Biere, [MaxSAT Fuzzing and Delta Debugging](https://cca.informatik.uni-freiburg.de/papers/PaxianBiere-JAIR26.pdf), JAIR 2026.
- Ke Xu, [Weighted Max-2-SAT Benchmarks with Hidden Optimum Solutions](https://rb-bench.github.io/benchmarks/weighted-max2sat.html).
- [CNFgen](https://massimolauria.net/cnfgen/), including [Pitfall](https://cnfgen.readthedocs.io/en/latest/cnfgen.families.pitfall.html) and [pebbling/Stone](https://cnfgen.readthedocs.io/en/latest/cnfgen.families.pebbling.html) generators.
- [MSE 2026 official release](https://zenodo.org/records/21358014).
- [SAT Competition official archive](https://zenodo.org/records/15125952), [SAT Competition 2026](https://satcompetition.github.io/2026/), and [SATLIB](https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html).
- [Generalization of Neural Combinatorial Solvers Through the Lens of Adversarial Robustness](https://github.com/johannaSommer/generalization-neural-co-solvers), ICLR 2022. This source provides a framework rather than a fixed universal corpus; MATT adapts generation and label-preserving perturbation ideas without claiming neural attack success or running downloaded models.

Third-party originals and code retain their source terms. No blanket license is assigned to the combined collection; the vendored CNFgen keeps its own license (`vendor/cnfgen-0.9.6.dist-info/licenses/`). Source archives, original identifiers, hashes, generator versions, and any available certificate claims are retained for attribution and future publication review.

## Citation

If you use MATT, please cite it as:

```
Pouya Ardehkhani. MATT: mathematical adversarial SAT/MaxSAT evaluation data, version 3.0 (2026).
https://github.com/pouyaardehkhani/MATT
```
