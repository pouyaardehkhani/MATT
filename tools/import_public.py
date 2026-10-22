"""Curate public source formulas, retaining original bytes and honest label evidence."""
from collections import Counter
import csv
import io
import re
import tarfile
from threading import Timer
from zipfile import ZipFile

from common import *
from pysat.solvers import Solver


def model_from_bits(bits,n):
    if not bits or any(c not in '01' for c in bits) or len(bits)<n: return None
    return [v if bits[v-1]=='1' else -v for v in range(1,n+1)]


def save_original(source_id,name,data):
    # Only archive content bytes are retained, never archive paths or executables.
    destination=ROOT/'sources'/'originals'/source_id/Path(name).name
    destination.parent.mkdir(parents=True,exist_ok=True); destination.write_bytes(data)
    return dict(original_path=destination.relative_to(ROOT).as_posix(),original_sha256=sha(data),original_filename=name,
                lineage_id=source_id+'/'+sha(data),retrieval_date='2026-10-16')


def main():
    rows=[]; specs=[]; exclusions=[]; seen=set()
    spec=scenario('public_maxsat_regressions','wcnf','Curated historical MaxSAT regression formulas',
        'A published minimized formula previously exposed a solver issue. The supplied metadata does not identify the precise root cause for every instance.',
        'Independent optimum checking can detect invalid cost or optimality claims on valid, nontrivial formulas. A historical issue is not a demonstrated failure of a current baseline.',
        origin='historical_regression',tier='historical')
    archive=ROOT/'sources'/'archives'/'regression-suite.zip'; count=0
    with ZipFile(archive) as z:
        metadata={}
        for name in ('allIssues.csv','MSE22+23Unique.csv'):
            for row in csv.DictReader((l for l in z.read(name).decode().splitlines() if not l.startswith('c ')),skipinitialspace=True): metadata[row['WCNFFile']]=row
        for name in sorted(metadata):
            md=metadata[name]
            try:
                if name.startswith('baseWCNFs/'): raise ValueError('Boundary-only source family')
                data=z.read(name); n,h,s,info=parse_text(decode(data),'wcnf')
                if not clean_for_math(h,s): raise ValueError('Tautology or repeated literal outside the main mathematical tier')
                if n<3 or not any(len(c)>1 for c in h+[c for _,c in s]): raise ValueError('Trivial unary-only formula')
                if not s or md['Satisfiable']!='SATISFIABLE': raise ValueError('No feasible nontrivial optimization objective')
                if sum(w for w,_ in s)>2**31-1 or max(w for w,_ in s)>10**7: raise ValueError('Numerical extreme excluded from semantic regression selection')
                source_cost=int(md['BestOValue'])
                if source_cost<=0: raise ValueError('Zero optimum excluded from positive-cost historical selection')
                key=sha(serialize(n,h,s,'wcnf'))
                if key in seen: raise ValueError('Duplicate normalized formula')
                witness=model_from_bits(md.get('Model'),n)
                if witness is None or assignment_cost(witness,h,s)!=source_cost: raise ValueError('Source witness missing or inconsistent with objective')
                if n<=18:
                    truth=evaluate(n,h,s)
                    if truth['optimum']!=source_cost: raise ValueError('Source optimum disagrees with exhaustive optimum')
                    truth['label_evidence']='exhaustive truth table; checked against source cost and witness'
                else:
                    truth=dict(status='OPTIMUM_REFERENCE' if md['CertifiedResult']=='YES' else 'FEASIBLE',
                        optimum=source_cost if md['CertifiedResult']=='YES' else None,best_known_cost=source_cost,
                        witness=witness,backbone=None,backbone_complete=False,
                        label_evidence='source_reports_certified_optimum; local witness checked' if md['CertifiedResult']=='YES' else 'source_best_known; local witness checked')
                source=save_original('maxsat-regression',name,data); source.update(url='https://maxsat-evaluations.github.io/2024/MaxSATRegressionSuiteWCNFs.zip',archive_path=archive.relative_to(ROOT).as_posix(),archive_member=name,
                    metadata=md,source_certificate_claim=md['CertifiedResult']=='YES',certificate_locally_checked=False,
                    documented_failure='historical regression membership; per-instance root cause not supplied in CSV')
                emit(rows,spec,count,'original',n,h,s,truth,dict(source_family=name.split('/')[0]),source)
                seen.add(key); count+=1
            except (ValueError,KeyError) as error: exclusions.append(dict(source='maxsat-regression',instance=name,reason=str(error)))
    spec.update(groups=count,examples=count); specs.append(spec); print(f'Imported semantic regression formulas: {count}',flush=True)
    # All 60 published hidden-optimum inputs, not 100 relabeled copies.
    spec=scenario('public_hidden_optimum_max2sat','wcnf','Published Model RB hidden-optimum formulas',
        'A hidden choice in each group avoids all heavy forbidden-pair penalties in a published Model RB instance.',
        'Larger constructed cores with stated optimum values broaden the size range; the maximized-satisfied objective is converted explicitly.',origin='public_benchmark',tier='external_reference')
    count=0
    for path in sorted((ROOT/'sources'/'archives').glob('frb*-wcnf.tar.gz')):
        with tarfile.open(path,'r:*') as tar:
            for member in sorted((m for m in tar.getmembers() if m.isfile() and m.name.endswith('.wcnf')),key=lambda m:m.name):
                data=tar.extractfile(member).read(); text=decode(data)
                header_repair=None
                try: n,h,s,info=parse_text(text,'wcnf')
                except ValueError as error:
                    if str(error)!='Header clause count mismatch': raise
                    # One published RB file has an incorrect clause count. Preserve its original bytes.
                    actual=sum(bool(line.strip()) and not line.startswith(('c','p')) for line in text.splitlines())
                    original_header=next(line for line in text.splitlines() if line.startswith('p '))
                    tokens=original_header.split(); old=int(tokens[3]); tokens[3]=str(actual)
                    text=text.replace(original_header,' '.join(tokens),1); n,h,s,info=parse_text(text,'wcnf')
                    header_repair=dict(original_declared_clauses=old,actual_clauses=actual,action='correct count in normalized copy only')
                groups,domain=map(int,re.search(r'frb(\d+)-(\d+)',member.name).groups())
                optimum_satisfied=int(re.search(r'optimum value\s*=\s*(\d+)',text).group(1)); total=sum(w for w,_ in s); converted_source_optimum=total-optimum_satisfied; optimum=n-groups
                assert not h and n==groups*domain
                # Check the lower-bound structure and seek a matching witness without an unbounded solve.
                penalties=[c for w,c in s if w!=1]; unit=[c for w,c in s if w==1]
                assert sorted(unit)==[[v] for v in range(1,n+1)] and all(w==n+1 for w,c in s if len(c)==2)
                pset={tuple(sorted(c)) for c in penalties}
                for g in range(groups):
                    for a in range(g*domain+1,(g+1)*domain+1):
                        for b in range(a+1,(g+1)*domain+1): assert tuple(sorted((-a,-b))) in pset
                with Solver(name='g4',bootstrap_with=penalties+[[v for v in range(g*domain+1,(g+1)*domain+1)] for g in range(groups)]) as solver:
                    solver.conf_budget(500 if n>500 else 5000)
                    timer=Timer(1.5,solver.interrupt); timer.start()
                    try: answer=solver.solve_limited(expect_interrupt=True); model=solver.get_model() if answer else None
                    finally: timer.cancel()
                annotation_issue=converted_source_optimum!=optimum
                truth=dict(status='OPTIMUM' if model else 'UNKNOWN' if annotation_issue else 'OPTIMUM_REFERENCE',optimum=optimum if model or not annotation_issue else None,backbone=None,backbone_complete=False,
                    label_evidence='group lower bound plus locally checked attaining witness' if model else 'source_reported_optimum; group lower bound locally checked; attaining witness not found within conflict budget')
                if model:
                    assert assignment_cost(model,h,s)==optimum; truth['witness']=model[:n]
                source=save_original('hidden-optimum-rb',member.name,data); source.update(url='https://rb-bench.github.io/benchmarks/weighted-max2sat.html',archive_path=path.relative_to(ROOT).as_posix(),archive_member=member.name,header_repair=header_repair,
                    source_objective='maximum_satisfied_soft_weight',source_optimum=optimum_satisfied,total_soft_weight=total,
                    converted_source_optimum=converted_source_optimum,source_annotation_inconsistent=annotation_issue,
                    conversion='minimum_violated_weight = total_soft_weight - source_maximum_satisfied_weight; inconsistent annotations replaced only when lower bound and attaining witness establish optimum')
                emit(rows,spec,count,'original',n,h,s,truth,dict(certificate='published_model_rb',groups=groups,domain=domain),source); count+=1
                if count%10==0: print(f'Published RB labels: {count}/60',flush=True)
    spec.update(groups=count,examples=count); specs.append(spec); print(f'Imported published hidden-optimum instances: {count}',flush=True)
    # SATLIB originals, including controlled-backbone families relevant to A.
    for archive in sorted((ROOT/'sources'/'archives').glob('satlib-*.tar.gz')):
        family=archive.name[len('satlib-'):-len('.tar.gz')]
        spec=scenario('satlib_'+family.lower(),'cnf','SATLIB '+family,
            'An established random or controlled-backbone CNF benchmark family from SATLIB.',
            'Adds nontrivial source cores for satisfiability/backbone evaluation; the source family name is preserved and full backbone labels are computed locally.',origin='public_benchmark',tier='application')
        count=0
        with tarfile.open(archive,'r:*') as tar:
            members=sorted((m for m in tar.getmembers() if m.isfile() and m.name.endswith('.cnf')),key=lambda m:m.name)[:120]
            for member in members:
                data=tar.extractfile(member).read()
                try: n,h,s,info=parse_text(decode(data),'cnf')
                except ValueError as error: exclusions.append(dict(source='satlib',instance=member.name,reason=str(error))); continue
                truth=sat_truth(n,h,True,budget=25000)
                expected='UNSAT' if family.startswith('uuf') else 'SAT'
                assert truth['status']==expected,(family,member.name,truth['status'])
                source=save_original('satlib-'+family,member.name,data); source.update(url='https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html',archive_path=archive.relative_to(ROOT).as_posix(),archive_member=member.name,source_status=expected)
                emit(rows,spec,count,'original',n,h,[],truth,dict(source_family=family),source); count+=1
        spec.update(groups=count,examples=count); specs.append(spec); print(f'Imported SATLIB {family}: {count}',flush=True)
        write_rows(ROOT/'parts'/'public.jsonl',rows); write_json(ROOT/'parts'/'public-scenarios.json',specs)
    # MSE selection: source labels remain distinguishable from locally established optima.
    selected=json.loads((ROOT/'sources'/'mse2026-selection.json').read_text())
    spec=scenario('mse2026_application_selection','wcnf','Diverse MSE 2026 application instances',
        'A stratified selection of smaller formulas from weighted and unweighted MSE 2026 archives, covering distinct application families.',
        'Provides real optimization structure and larger scale. Competition reference optima and best-known bounds are retained separately.',origin='public_benchmark',tier='external_reference')
    count=0
    for entry in selected:
        path=ROOT/entry['path']; md=entry['metadata']; data=path.read_bytes()
        try: n,h,s,info=parse_text(decode(data),'wcnf')
        except (ValueError,UnicodeDecodeError) as error: exclusions.append(dict(source='mse2026',instance=entry['path'],reason=str(error))); continue
        if not s or not clean_for_math(h,s): exclusions.append(dict(source='mse2026',instance=entry['path'],reason='No soft clauses or noncanonical clause content')); continue
        optimal=md.get('optimal_cost','unknown'); best=md.get('best_known_cost','unknown')
        truth=dict(status='OPTIMUM_REFERENCE' if optimal!='unknown' else 'REFERENCE_ONLY',optimum=int(optimal) if optimal!='unknown' else None,
            best_known_cost=int(best) if best!='unknown' else None,backbone=None,backbone_complete=False,label_evidence='MSE2026 source metadata; no local optimum proof')
        source=dict(url=entry['url'],archive_member=entry['archive_member'],original_path=entry['path'],original_sha256=sha(data),metadata=md,
            lineage_id='mse2026/'+md['hash'],retrieval_date='2026-10-16',certificate_locally_checked=False)
        emit(rows,spec,count,'original',n,h,s,truth,dict(source_family=md.get('family')),source); count+=1
    spec.update(groups=count,examples=count); specs.append(spec); print(f'Imported MSE 2026 selection: {count}',flush=True)
    # Competition files may have UNKNOWN labels: never manufacture SAT status or backbone.
    sat_selection=ROOT/'sources'/'satcomp2026-selection.json'
    if sat_selection.exists():
        spec=scenario('satcomp2026_application_selection','cnf','SAT Competition 2026 originals',
            'A bounded-size selection of actual main-track competition formulas with their GBD identities and source results.',
            'Extends structural diversity; unknown source status and missing backbone labels are explicit.',origin='public_benchmark',tier='external_reference')
        count=0
        for entry in json.loads(sat_selection.read_text()):
            try:
                path=ROOT/entry['path']; data=path.read_bytes(); n,h,s,info=parse_text(decode(data),'cnf')
            except (ValueError,UnicodeDecodeError) as error: exclusions.append(dict(source='satcomp2026',instance=entry['path'],reason=str(error))); continue
            cells=entry['gbd']['cells']; status=cells[4].upper() if len(cells)>4 else 'UNKNOWN'
            truth=dict(status=status if status in ('SAT','UNSAT') else 'UNKNOWN',backbone=None,backbone_complete=False,label_evidence='GBD source result; not locally proved')
            source=dict(url=entry['url'],original_path=entry['path'],original_sha256=sha(data),gbd=entry['gbd'],lineage_id='satcomp2026/'+entry['gbd']['hash'],retrieval_date='2026-10-16')
            emit(rows,spec,count,'original',n,h,[],truth,dict(source_family=cells[2] if len(cells)>2 else None),source); count+=1
        if count: spec.update(groups=count,examples=count); specs.append(spec)
        print(f'Imported SAT Competition: {count}',flush=True)
    write_rows(ROOT/'parts'/'public.jsonl',rows); write_json(ROOT/'parts'/'public-scenarios.json',specs)
    write_json(ROOT/'sources'/'exclusions.json',exclusions)
    print(f'Public formulas: {len(rows)}; excluded source entries: {len(exclusions)}',flush=True)


if __name__=='__main__': main()
