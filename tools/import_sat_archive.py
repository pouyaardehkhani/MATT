"""Add actual SAT Competition archive members without repeating other imports."""
from common import *


def main():
    rows=read_rows(ROOT/'parts'/'public.jsonl'); specs=json.loads((ROOT/'parts'/'public-scenarios.json').read_text())
    sid='satcompetition_archive_selection'; rows=[r for r in rows if r['scenario_id']!=sid]; specs=[s for s in specs if s['id']!=sid]
    spec=scenario(sid,'cnf','SAT Competition archive originals, including 2026 selections',
        'Actual competition CNFs selected from the official 2002–2024 archive; matching GBD hashes identify those also selected in the 2026 main track.',
        'Adds established application and crafted structure at realistic sizes. Unknown status and missing backbone labels are explicit; the 2026 file endpoint timed out, so identical identities were retrieved from the official archive.',
        origin='public_benchmark',tier='external_reference')
    excluded=[]; count=0
    for entry in json.loads((ROOT/'sources'/'satcompetition-archive-selection.json').read_text()):
        data=(ROOT/entry['path']).read_bytes()
        try: n,h,s,info=parse_text(decode(data),'cnf')
        except (ValueError,UnicodeDecodeError) as error:
            excluded.append(dict(source='satcompetition-archive',instance=entry['archive_member'],reason=str(error))); continue
        source_status=entry['gbd']['cells'][4].upper() if entry.get('gbd') else 'UNKNOWN'
        if n<=5000 and len(h)<=100000:
            truth=sat_truth(n,h,backbone=n<=150,budget=10000,time_budget=1)
        else: truth=dict(status='UNKNOWN',backbone=None,backbone_complete=False,label_evidence='not solved locally; size selection limit for labeling')
        locally_established=truth['status']!='UNKNOWN'
        if locally_established and source_status in ('SAT','UNSAT'): assert truth['status']==source_status
        if not locally_established and source_status in ('SAT','UNSAT'):
            truth.update(status=source_status,label_evidence='GBD source result; local status not established')
        source=dict(url=entry['url'],archive_member=entry['archive_member'],original_path=entry['path'],original_sha256=sha(data),gbd_hash=entry['gbd_hash'],gbd=entry.get('gbd'),also_in_main_2026=entry['also_in_main_2026'],
            source_status=source_status,absolute_label_locally_established=locally_established,lineage_id='gbd/'+str(entry['gbd_hash']),retrieval_date='2026-10-16')
        emit(rows,spec,count,'original',n,h,[],truth,dict(source_family=entry['gbd']['cells'][2] if entry.get('gbd') else entry['archive_member'].split('-')[0]),source); count+=1
        if count%20==0: print(f'Imported competition originals: {count}',flush=True)
    spec.update(groups=count,examples=count); specs.append(spec)
    write_rows(ROOT/'parts'/'public.jsonl',rows); write_json(ROOT/'parts'/'public-scenarios.json',specs)
    write_json(ROOT/'sources'/'satcompetition-exclusions.json',excluded)
    print(f'Competition originals added: {count}')


if __name__=='__main__': main()
