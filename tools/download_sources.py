"""Fetch public source material; never execute downloaded programs or installers."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
ARCHIVES=ROOT/'sources'/'archives'


def fetch(url,path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        last=None
        for attempt in range(3):
            try:
                request=urllib.request.Request(url,headers={'User-Agent':'MATT-research-dataset/3.0'})
                with urllib.request.urlopen(request,timeout=60) as response:
                    data=response.read()
                path.write_bytes(data); break
            except Exception as error:
                last=error
                if attempt==2: raise
                time.sleep(1)
    data=path.read_bytes()
    return dict(url=url,path=path.relative_to(ROOT).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def main():
    tasks=[
      ('https://maxsat-evaluations.github.io/2024/MaxSATRegressionSuiteWCNFs.zip','regression-suite.zip'),
      ('https://codeload.github.com/tobipaxe/MaxSATRegressionSuite/zip/refs/heads/main','regression-tools.zip'),
      ('https://codeload.github.com/MassimoLauria/cnfgen/zip/refs/heads/master','cnfgen-source.zip'),
      ('https://codeload.github.com/johannaSommer/generalization-neural-co-solvers/zip/refs/heads/main','neural-robustness-source.zip'),
      ('https://zenodo.org/records/21358014/files/benchmark-metadata.csv?download=1','mse2026-metadata.csv'),
      ('https://satcompetition.github.io/2026/downloads.html','satcomp2026-downloads.html'),
      ('https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html','satlib-index.html'),
    ]
    for stem in ('10-6','15-9','20-11','25-13','30-15','35-17','40-19','45-21','50-23','53-24','56-25','59-26'):
        name=f'frb{stem}-wcnf.tar.gz'
        tasks.append((f'https://rb-bench.github.io/assets/bench/{name}',name))
    records=[]; failures=[]
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs={pool.submit(fetch,url,ARCHIVES/name):(url,name) for url,name in tasks}
        for future in as_completed(jobs):
            url,name=jobs[future]
            try:
                row=future.result(); records.append(row); print(f'Fetched {name}: {row["bytes"]} bytes',flush=True)
            except Exception as error:
                failures.append(dict(url=url,name=name,error=str(error))); print(f'FAILED {name}: {error}',flush=True)
    records.sort(key=lambda r:r['path'])
    (ROOT/'sources'/'downloads.json').write_text(json.dumps(dict(retrieval_date='2026-10-16',files=records,failures=failures),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(files=len(records),failures=failures),indent=2))


if __name__=='__main__': main()
