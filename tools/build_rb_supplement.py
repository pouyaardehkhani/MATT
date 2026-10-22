"""Supply 60 genuinely new hidden-optimum cores alongside the 60 published originals."""
import itertools
import math
import random
from common import *


def main():
    spec=scenario('public_hidden_optimum_max2sat','wcnf','Published and independently generated hidden-optimum Max-2-SAT',
        'The published Model RB collection is supplemented by new independently seeded group/forbidden-pair instances with explicit planted optimum witnesses.',
        'The same mathematical scenario has at least 120 independent cores without pretending that 60 generated inputs were downloaded originals.',origin='adapted_generator',tier='scaled')
    rows=[]
    for index in range(60,120):
        rng=random.Random(int(sha(f'20261016/published-rb-supplement/{index}'.encode())[:16],16))
        groups=rng.randint(8,40); domain=rng.randint(5,20); n=groups*domain; planted=[g*domain+rng.randrange(domain)+1 for g in range(groups)]
        forbidden=set()
        for g in range(groups): forbidden.update(itertools.combinations(range(g*domain+1,(g+1)*domain+1),2))
        for _ in range(int(groups*math.log(groups)*domain*1.5)):
            a,b=sorted(rng.sample(range(1,n+1),2))
            if (a-1)//domain!=(b-1)//domain and not (a in planted and b in planted): forbidden.add((a,b))
        soft=[(1,[v]) for v in range(1,n+1)]+[(n+1,[-a,-b]) for a,b in sorted(forbidden)]
        model=[v if v in planted else -v for v in range(1,n+1)]
        assert assignment_cost(model,[],soft)==n-groups
        truth=dict(status='OPTIMUM',optimum=n-groups,witness=model,backbone=None,backbone_complete=False,
            label_evidence='group lower-bound certificate plus checked planted attaining witness; independently generated supplement')
        source=dict(url='https://rb-bench.github.io/benchmarks/weighted-max2sat.html',
            adaptation='new seeded formula from the published mathematical model, not an imported original',
            lineage_id=f'rb-supplement/{index}',retrieval_date=None)
        params=dict(certificate='model_rb',groups=groups,domain=domain,planted=planted,penalty=n+1,no_disjoint_filler=True,
            published_collection_supplement=True)
        emit(rows,spec,index,'generated_supplement',n,[],soft,truth,params,source)
    write_rows(ROOT/'parts'/'rb-supplement.jsonl',rows)
    print('Generated 60 additional independent hidden-optimum cores; published-original count remains 60.')


if __name__=='__main__': main()
