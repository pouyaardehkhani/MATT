# Source material and acquisition record

`file-inventory.json` records the SHA256 and size of every retained archive and original. Per-formula provenance is in the root manifest. Original bytes are preserved separately from normalized evaluation formulas.

- MaxSAT regression: exact public archive plus source CSVs. `exclusions.json` explains mathematical-tier filtering; no removed source archive was altered.
- Hidden-optimum Max-2-SAT: all 12 published archives and all 60 originals. `source-discrepancies.json` documents the one inconsistent original and the evidence for its normalized reference answer.
- CNFgen: downloaded source snapshot for reference, plus exact locally used 0.9.6 package code and license under `vendor`. The installed generator version, not an unversioned web snapshot, produced the instances. The Pitfall signed-offset correction is isolated in the MATT adapter; unadapted generated originals and a counterexample witness are retained in `generator-corrections.json` and `originals/cnfgen-pitfall-unadapted`.
- Neural adversarial framework: original source archive retained; the dataset uses standalone adapted generation/perturbation ideas. No downloaded neural model or installer was executed.
- MSE 2026: official metadata and 140 selected original compressed ZIP members; 134 meet the normalized mathematical-tier filter. `mse2026-selection.json` records exact archive/member identity.
- SATLIB: six archives, with 120 original instances selected from each. Original family names are retained.
- SAT Competition: the 2026 GBD table and URI are retained. Direct instance downloads timed out, so a published official archive plus its GBD hash map supplied 120 actual competition originals. `satcompetition-archive-selection.json` states which are also selected for 2026. `integrity.json` records the count. This is not a claim that 120 new 2026 submissions were downloaded.

Some source collections lack an explicit dataset redistribution license in their front-page documentation. Their original terms and attribution remain attached to the source; this combined collection does not relicense them. CNFgen's retained code carries its GPL license, and the neural framework source archive includes its own license. Review source terms when preparing a public redistribution.
