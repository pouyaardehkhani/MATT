"""Inventory retained originals/archives and verify split lineage integrity."""
from collections import Counter, defaultdict
from common import *


def main():
    rows=read_rows(ROOT/'manifest.jsonl'); files=[]
    for folder in ('sources/archives','sources/originals'):
        for path in sorted((ROOT/folder).rglob('*')):
            if path.is_file(): files.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes())))
    write_json(ROOT/'sources'/'file-inventory.json',dict(retrieval_date='2026-10-16',files=files))
    hashes=defaultdict(set); lineages=defaultdict(set); components=defaultdict(set)
    for r in rows:
        hashes[r['sha256']].add(r['split']); components[r['split_lineage_component']].add(r['split'])
        if lineage:=r.get('source',{}).get('lineage_id'): lineages[lineage].add(r['split'])
    assert all(len(v)==1 for v in hashes.values())
    assert all(len(v)==1 for v in lineages.values())
    assert all(len(v)==1 for v in components.values())
    checked_archive=json.loads((ROOT/'sources'/'satcompetition-archive-selection.json').read_text())
    rb=[r for r in rows if r['scenario_id']=='public_hidden_optimum_max2sat' and r['origin']=='public_benchmark']
    discrepancies=[dict(id=r['id'],original=r['source']['original_path'],header_repair=r['source'].get('header_repair'),annotation_inconsistent=r['source'].get('source_annotation_inconsistent'),reference_optimum=r['truth'].get('optimum'),evidence=r['truth']['label_evidence']) for r in rb if r['source'].get('header_repair') or r['source'].get('source_annotation_inconsistent')]
    write_json(ROOT/'sources'/'source-discrepancies.json',discrepancies)
    report=dict(status='PASS',retained_source_files=len(files),retained_source_bytes=sum(r['bytes'] for r in files),
        normalized_formula_bytes=sum((ROOT/r['path']).stat().st_size for r in rows),
        identical_formula_split_leaks=0,source_lineage_split_leaks=0,
        source_lineages=len(lineages),split_lineage_components=len(components),
        competition_archive_originals=len(checked_archive),also_in_2026_selection=sum(r['also_in_main_2026'] for r in checked_archive),
        published_rb_originals=len(rb),published_rb_locally_attained_optima=sum(r['truth']['status']=='OPTIMUM' for r in rb),
        source_discrepancies=len(discrepancies),manifest_sha256=sha((ROOT/'manifest.jsonl').read_bytes()))
    write_json(ROOT/'integrity.json',report)
    (ROOT/'sources'/'INDEX.md').write_text('''# Source material and acquisition record

`file-inventory.json` records the SHA256 and size of every retained archive and original. Per-formula provenance is in the root manifest. Original bytes are preserved separately from normalized evaluation formulas.

- MaxSAT regression: exact public archive plus source CSVs. `exclusions.json` explains mathematical-tier filtering; no removed source archive was altered.
- Hidden-optimum Max-2-SAT: all 12 published archives and all 60 originals. `source-discrepancies.json` documents the one inconsistent original and the evidence for its normalized reference answer.
- CNFgen: downloaded source snapshot for reference, plus exact locally used 0.9.6 package code and license under `vendor`. The installed generator version, not an unversioned web snapshot, produced the instances. The Pitfall signed-offset correction is isolated in the MATT adapter; unadapted generated originals and a counterexample witness are retained in `generator-corrections.json` and `originals/cnfgen-pitfall-unadapted`.
- Neural adversarial framework: original source archive retained; the dataset uses standalone adapted generation/perturbation ideas. No downloaded neural model or installer was executed.
- MSE 2026: official metadata and 140 selected original compressed ZIP members; 134 meet the normalized mathematical-tier filter. `mse2026-selection.json` records exact archive/member identity.
- SATLIB: six archives, with 120 original instances selected from each. Original family names are retained.
- SAT Competition: the 2026 GBD table and URI are retained. Direct instance downloads timed out, so a published official archive plus its GBD hash map supplied 120 actual competition originals. `satcompetition-archive-selection.json` states which are also selected for 2026. `integrity.json` records the count. This is not a claim that 120 new 2026 submissions were downloaded.

Some source collections lack an explicit dataset redistribution license in their front-page documentation. Their original terms and attribution remain attached to the source; this combined collection does not relicense them. CNFgen's retained code carries its GPL license, and the neural framework source archive includes its own license. Review source terms when preparing a public redistribution.
''',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
