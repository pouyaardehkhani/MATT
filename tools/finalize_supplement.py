"""Validate an append-only supplement against a completed, unchanged base audit.

This rehashes every preserved formula and source original, requires byte-identical
old row metadata and unchanged verifier/construction code, and fully checks each
new mathematical certificate. If any premise changes, run verify_all.py instead.
"""
from collections import Counter
import contextlib
import io
import json
import shutil
import time
from common import *
import assemble
from verify_all import certificate


def main():
    started=time.time(); old_bytes=(ROOT/'manifest.jsonl').read_bytes(); old_rows=read_rows(ROOT/'manifest.jsonl')
    prior=json.loads((ROOT/'validation.json').read_text())
    assert prior.get('version')=='3.0.0' and prior['status']=='PASS'
    assert prior['manifest_sha256']==sha(old_bytes) and prior['formulas']==len(old_rows)
    for name,expected in prior['source_hashes'].items(): assert sha((ROOT/name).read_bytes())==expected,name
    previous_local={r['id'] for r in read_rows(ROOT/'views'/'locally-established-labels.jsonl')}
    archived=ROOT/'releases'/'v3-base-audit'; archived.mkdir(parents=True,exist_ok=True)
    (archived/'manifest.jsonl').write_bytes(old_bytes); shutil.copy2(ROOT/'validation.json',archived/'validation.json')
    with contextlib.redirect_stdout(io.StringIO()): assemble.main()
    rows=read_rows(ROOT/'manifest.jsonl'); by_id={r['id']:r for r in rows}; previous={r['id']:r for r in old_rows}
    assert all(by_id.get(key)==row for key,row in previous.items()),'Existing row metadata changed; run full audit'
    stats=Counter(prior['checks']); originals={}; new=[]
    for row in rows:
        data=(ROOT/row['path']).read_bytes(); assert sha(data)==row['sha256'],row['id']
        if source:=row.get('source'):
            if 'original_path' in source:
                path=source['original_path']
                if path not in originals: originals[path]=sha((ROOT/path).read_bytes())
                assert originals[path]==source['original_sha256']
        if row['id'] in previous: continue
        assert row['parameters'].get('published_collection_supplement') is True
        n,h,s,_=parse_text(decode(data),'wcnf'); assert n==row['nvars'] and len(h)+len(s)==row['nclauses']
        truth=row['truth']; assert truth['status']=='OPTIMUM' and assignment_cost(truth['witness'],h,s)==truth['optimum']
        assert certificate(row,n,h,s,stats)
        new.append(row); previous_local.add(row['id'])
        stats['strict_formula_and_sha256_checks']+=1; stats['witness_and_original_objective_checks']+=1
    assert len(new)==60
    specs=json.loads((ROOT/'scenarios.json').read_text())['scenarios']; grouped={r['group_id'] for r in rows}
    for spec in specs:
        chosen=[r for r in rows if r['scenario_id']==spec['id']]
        assert len(chosen)==spec['examples'] and len({r['group_id'] for r in chosen})==spec['groups']>=100
    write_rows(ROOT/'views'/'locally-established-labels.jsonl',[r for r in rows if r['id'] in previous_local])
    write_rows(ROOT/'views'/'reference-only.jsonl',[r for r in rows if r['id'] not in previous_local])
    write_rows(ROOT/'views'/'maxsat-optimum-local.jsonl',[r for r in rows if r['id'] in previous_local and r['truth'].get('optimum') is not None])
    write_rows(ROOT/'views'/'sat-status-local.jsonl',[r for r in rows if r['id'] in previous_local and r['format']=='dimacs-cnf' and r['truth']['status'] in ('SAT','UNSAT')])
    report=prior.copy(); report.update(formulas=len(rows),groups=len(grouped),scenarios=len(specs),checks=dict(stats),
        locally_established_label_rows=len(previous_local),reference_only_or_source_claim_rows=len(rows)-len(previous_local),
        evidence_categories=dict(Counter(r.get('label_evidence','v2_exhaustive') for r in rows)),origins=dict(Counter(r['origin'] for r in rows)),
        manifest_sha256=sha((ROOT/'manifest.jsonl').read_bytes()),
        append_only_audit=dict(base_report='releases/v3-base-audit/validation.json',base_manifest_sha256=prior['manifest_sha256'],
            unchanged_prior_rows=len(old_rows),preserved_formula_bytes_rehashed=True,original_source_files_rehashed=len(originals),
            new_formulas_fully_checked=len(new),all_scenarios_have_at_least_100_groups=True,
            elapsed_seconds=round(time.time()-started,3)))
    report['source_hashes'].update({f'tools/{name}':sha((ROOT/'tools'/name).read_bytes()) for name in ('finalize_supplement.py','build_rb_supplement.py')})
    write_json(ROOT/'validation.json',report)
    print(json.dumps({k:report[k] for k in ('status','formulas','groups','scenarios','locally_established_label_rows','reference_only_or_source_claim_rows','append_only_audit')},indent=2))


if __name__=='__main__': main()
