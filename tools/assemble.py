"""Assemble a versioned manifest without changing existing formula bytes."""
from collections import Counter, defaultdict
from common import *


def main():
    core=read_rows(ROOT/'releases'/'v2'/'manifest.jsonl')
    specs=json.loads((ROOT/'releases'/'v2'/'scenarios.json').read_text())['scenarios']
    for r in core:
        r.update(origin='constructed_v2',tier='exhaustive_core',label_evidence='exhaustive truth table; independent MiniSat22/RC2 checks in v2 audit')
        r['truth']['backbone_complete']=True
        # Keep the exact v2 truth object for rechecking; label scope is recorded outside it.
        r['truth'].pop('backbone_complete')
        r['backbone_complete']=True
    for s in specs: s.update(origin='constructed_v2',tier='exhaustive_core')
    rows=core[:]
    for stem,cat in [('extensions','extension-scenarios'),('public','public-scenarios'),('application-pairs','application-pair-scenarios')]:
        rows.extend(read_rows(ROOT/'parts'/f'{stem}.jsonl'))
        specs.extend(json.loads((ROOT/'parts'/f'{cat}.json').read_text()))
    if (ROOT/'parts'/'rb-supplement.jsonl').exists():
        supplement=read_rows(ROOT/'parts'/'rb-supplement.jsonl'); rows.extend(supplement)
        entry=next(s for s in specs if s['id']=='public_hidden_optimum_max2sat')
        entry.update(groups=entry['groups']+len(supplement),examples=entry['examples']+len(supplement),
            title='Published hidden-optimum Max-2-SAT with independent supplements',published_originals=60,independently_generated_supplements=len(supplement),
            scenario='60 published Model RB hidden-optimum originals plus 60 new independently seeded cores using the same mathematical model.',
            rationale='Provides 120 independent examples of the scenario while preserving the distinction between original published inputs and generated supplements.')
    for s in specs:
        s.setdefault('origin','constructed'); s.setdefault('tier','extended')
    assert len({r['id'] for r in rows})==len(rows)
    # Same source originals and byte-identical formulas share a split, including all controlled descendants.
    parent={r['group_id']:r['group_id'] for r in rows}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[max(a,b)]=min(a,b)
    seen_bytes={}; seen_lineages={}; duplicate_records=[]
    for r in rows:
        key=r['sha256']
        if key in seen_bytes:
            original=seen_bytes[key]; union(r['group_id'],original['group_id']); r['duplicate_formula_of']=original['id']
            duplicate_records.append(dict(id=r['id'],duplicate_formula_of=original['id'],sha256=key))
        else: seen_bytes[key]=r
        lineage=r.get('source',{}).get('lineage_id')
        if lineage:
            if lineage in seen_lineages: union(r['group_id'],seen_lineages[lineage])
            else: seen_lineages[lineage]=r['group_id']
    for r in rows:
        component=find(r['group_id']); bucket=int(sha(component.encode())[:8],16)%10
        r['split']='train' if bucket<6 else 'dev' if bucket<8 else 'test'; r['split_lineage_component']=component
    write_rows(ROOT/'manifest.jsonl',rows)
    pairs=[]
    grouped=defaultdict(list)
    for r in rows: grouped[r['group_id']].append(r)
    for gid,members in grouped.items():
        variants={r['variant']:r for r in members}
        record=dict(group_id=gid,scenario_id=members[0]['scenario_id'],split=members[0]['split'],origin=members[0]['origin'],paths=[r['path'] for r in members],member_ids=[r['id'] for r in members])
        if 'control' in variants and 'challenge' in variants:
            a,b=variants['control'],variants['challenge']; record.update(control_status=a['truth']['status'],challenge_status=b['truth']['status'],control_optimum=a['truth'].get('optimum'),challenge_optimum=b['truth'].get('optimum'),intervention=b['intervention'],relation=b.get('relation_to_control'))
            if a['truth'].get('optimum') is not None and b['truth'].get('optimum') is not None: record['optimum_delta']=b['truth']['optimum']-a['truth']['optimum']
        pairs.append(record)
    write_rows(ROOT/'pairs.jsonl',pairs)
    write_json(ROOT/'scenarios.json',dict(version='3.0.0',master_seed=20261016,scenarios=specs))
    summary=dict(version='3.0.0',date='2026-10-16',scenarios=len(specs),groups=len(grouped),formula_records=len(rows),
        unique_formula_bytes=len(seen_bytes),duplicate_formula_records=len(duplicate_records),
        counts=dict(Counter('cnf' if r['format']=='dimacs-cnf' else 'wcnf' for r in rows)),origins=dict(Counter(r['origin'] for r in rows)),
        tiers=dict(Counter(r['tier'] for r in rows)),statuses=dict(Counter(r['truth']['status'] for r in rows)),
        nvars_min=min(r['nvars'] for r in rows),nvars_max=max(r['nvars'] for r in rows),
        scaled_constructed_nvars_max=max(r['nvars'] for r in rows if r['tier']=='scaled'),
        splits=dict(Counter(r['split'] for r in rows)),source_collections=[dict(id=s['id'],groups=s['groups'],examples=s['examples']) for s in specs if s['origin']=='public_benchmark' or s['origin']=='historical_regression'],
        constructed_scenarios=sum(s['origin'] not in ('public_benchmark','historical_regression') for s in specs),
        physical_membership='manifest paths only; legacy_v1 and sources archives are excluded',baseline_experiments_run=0,
        completeness='Expanded coverage release, not a guarantee against all possible inputs or methods.')
    write_json(ROOT/'summary.json',summary); write_rows(ROOT/'sources'/'duplicate-formulas.jsonl',duplicate_records)
    views=ROOT/'views'; views.mkdir(exist_ok=True)
    write_rows(views/'cnf.jsonl',[r for r in rows if r['format']=='dimacs-cnf'])
    write_rows(views/'wcnf.jsonl',[r for r in rows if r['format']=='wcnf-old'])
    write_rows(views/'reference-only.jsonl',[r for r in rows if r['truth']['status'] in ('OPTIMUM_REFERENCE','REFERENCE_ONLY','UNKNOWN')])
    write_rows(views/'large-instances.jsonl',[r for r in rows if r['nvars']>=200])
    write_rows(views/'complete-backbones.jsonl',[r for r in rows if r['format']=='dimacs-cnf' and r['truth']['status']=='SAT' and r['truth'].get('backbone_complete',r.get('backbone_complete',False)) and r['truth'].get('backbone_scope')!='primary_variables_only'])
    lines=['# MATT v3 scenario catalogue','',f'{len(specs)} scenarios and source collections. Count groups before representation variants. Published originals retain their actual available counts; no copied originals are presented as independent examples.','']
    for s in specs:
        lines += [f"## {s['id']}: {s['title']}",'',f"- Origin: {s['origin']}; format: {s['family']}; groups: {s['groups']}; records: {s['examples']}.",f"- Scenario: {s['scenario']}",f"- Rationale: {s['rationale']}",f"- Intervention: {s.get('intervention','None; original source formula')}",'']
    (ROOT/'scenarios.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
