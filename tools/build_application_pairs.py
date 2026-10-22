"""Controlled, proof-carrying derivatives of distinct imported benchmark originals."""
import random
from common import *


def main():
    public=read_rows(ROOT/'parts'/'public.jsonl'); rows=[]; specs=[]
    spec=scenario('application_resolution_amplification','cnf','Resolution-implied additions to imported CNFs',
        'A genuine SATLIB benchmark gains clauses obtained by one-step resolution of existing clauses.',
        'The added constraints can change heuristic features but preserve every model and the complete original backbone. Each addition carries its two parent indices and pivot.',
        'Append checked non-tautological resolvents.',origin='controlled_derivative',tier='application')
    candidates=[r for r in public if r['scenario_id'].startswith('satlib_') and r['truth']['status']=='SAT' and r['truth'].get('backbone_complete')]
    # Spread the selection across the four satisfiable source families.
    buckets={sid:[r for r in candidates if r['scenario_id']==sid] for sid in sorted({r['scenario_id'] for r in candidates})}
    chosen=[]
    for i in range(120):
        key=sorted(buckets)[i%len(buckets)]; chosen.append(buckets[key][i//len(buckets)])
    for i,parent in enumerate(chosen):
        n,h,s,_=parse_text(decode((ROOT/parent['path']).read_bytes()),'cnf'); rng=random.Random(i+20261016)
        existing={tuple(sorted(c)) for c in h}; additions=[]; proof=[]
        for a,ca in enumerate(h):
            for pivot in ca:
                for b,cb in enumerate(h):
                    if a==b or -pivot not in cb: continue
                    resolvent=sorted((set(ca)-{pivot})|(set(cb)-{-pivot}))
                    key=tuple(resolvent)
                    if not resolvent or key in existing or any(-l in resolvent for l in resolvent): continue
                    additions.append(resolvent); proof.append(dict(parent_indices=[a,b],pivot=pivot,resolvent=resolvent)); existing.add(key)
                    if len(additions)>=5: break
                if len(additions)>=5: break
            if len(additions)>=5: break
        assert additions
        params=dict(certificate='resolution_implication',parent_manifest_id=parent['id'],resolution_steps=proof,added_clauses=additions)
        emit(rows,spec,i,'control',n,h,[],parent['truth'],params,parent['source'])
        emit(rows,spec,i,'challenge',n,h+additions,[],parent['truth'],params,parent['source'],dict(type='full_model_equivalence',parent_id=parent['id']))
    spec.update(groups=120,examples=240); specs.append(spec); print('Built 120 resolution-amplification application pairs',flush=True)
    spec=scenario('application_objective_scaling','wcnf','Exact objective scaling on real MaxSAT applications',
        'An imported MSE 2026 application formula is reweighted by a positive integer factor.',
        'Every feasible assignment cost scales exactly, giving a checkable relation on real problem structure. Source-only absolute optimum claims remain source-only.',
        'Multiply all soft weights while retaining every hard constraint.',origin='controlled_derivative',tier='external_reference')
    parents=[r for r in public if r['scenario_id']=='mse2026_application_selection'][:120]
    assert len(parents)==120
    for i,parent in enumerate(parents):
        n,h,s,_=parse_text(decode((ROOT/parent['path']).read_bytes()),'wcnf'); scale=2+i%11; truth=parent['truth'].copy()
        for key in ('optimum','best_known_cost'):
            if truth.get(key) is not None: truth[key]*=scale
        truth['label_evidence']='source absolute label; exact pointwise scaling relation locally established'
        params=dict(certificate='source_weight_scaling',parent_manifest_id=parent['id'],scale=scale)
        emit(rows,spec,i,'control',n,h,s,parent['truth'],params,parent['source'])
        emit(rows,spec,i,'challenge',n,h,[(w*scale,c) for w,c in s],truth,params,parent['source'],dict(type='optimum_scaling',factor=scale,parent_id=parent['id']))
    spec.update(groups=120,examples=240); specs.append(spec)
    write_rows(ROOT/'parts'/'application-pairs.jsonl',rows); write_json(ROOT/'parts'/'application-pair-scenarios.json',specs)
    print('Built 120 real-application scaling pairs',flush=True)


if __name__=='__main__': main()
