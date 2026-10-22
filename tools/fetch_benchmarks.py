"""Download bounded selections from official archives, retaining exact source bytes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import io
import json
from pathlib import Path
import re
import urllib.request
from zipfile import ZipFile

from download_sources import ROOT, ARCHIVES, fetch


class RemoteZip(io.RawIOBase):
    def __init__(self,url):
        self.url=url; self.pos=0
        req=urllib.request.Request(url,method='HEAD')
        with urllib.request.urlopen(req,timeout=60) as response: self.size=int(response.headers['Content-Length'])
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        return self.pos
    def read(self,size=-1):
        if size<0: size=self.size-self.pos
        if size==0 or self.pos>=self.size: return b''
        end=min(self.size-1,self.pos+size-1)
        for attempt in range(4):
            request=urllib.request.Request(self.url+f'&matt_range={self.pos}-{end}&retry={attempt}',headers={'Range':f'bytes={self.pos}-{end}'})
            try:
                with urllib.request.urlopen(request,timeout=45) as response:
                    if response.status!=206: raise RuntimeError('Server did not honor byte range; refusing full archive download')
                    data=response.read(size+1)
                break
            except Exception:
                if attempt==3: raise
        if len(data)>size: raise RuntimeError('Unexpected range length')
        self.pos+=len(data); return data


def mse():
    metadata={r['hash']:r for r in csv.DictReader((ARCHIVES/'mse2026-metadata.csv').read_text().splitlines())}
    all_records=[]
    for track in ('anytime-unweighted','anytime-weighted'):
        name=f'benchmarks-{track}.zip'; url=f'https://zenodo.org/records/21358014/files/{name}?download=1'
        remote=RemoteZip(url)
        with ZipFile(remote) as archive:
            infos=sorted((x for x in archive.infolist() if x.filename.endswith('.wcnf.xz')),key=lambda x:(x.file_size,x.filename))
            # Prefer family diversity, then fill from the smaller sources. This is an explicit selection, not the whole MSE archive.
            selected=[]; families=set()
            for info in infos:
                key=Path(info.filename).name.split('.')[0]; family=metadata.get(key,{}).get('family','unknown')
                if family not in families and info.file_size<=2_000_000:
                    selected.append(info); families.add(family)
            for info in infos:
                if len(selected)>=70: break
                if info not in selected and info.file_size<=2_000_000: selected.append(info)
            for i,info in enumerate(selected):
                dest=ROOT/'sources'/'originals'/'mse2026'/Path(info.filename).name
                dest.parent.mkdir(parents=True,exist_ok=True)
                if not dest.exists(): dest.write_bytes(archive.read(info))
                key=dest.name.split('.')[0]
                all_records.append(dict(url=url,archive_member=info.filename,path=dest.relative_to(ROOT).as_posix(),metadata=metadata.get(key,{})))
                if i%10==0: print(f'MSE {track}: {i+1}/{len(selected)}',flush=True)
    (ROOT/'sources'/'mse2026-selection.json').write_text(json.dumps(all_records,indent=2)+'\n',encoding='utf-8')


def sat_sources():
    tasks=[]
    for name in ('uf50-218','uuf50-218','uf100-430','uuf100-430','CBS_k3_n100_m403_b10','CBS_k3_n100_m403_b90'):
        folder='CBS' if name.startswith('CBS') else 'RND3SAT'
        tasks.append((f'https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/{folder}/{name}.tar.gz',ARCHIVES/f'satlib-{name}.tar.gz'))
    tasks += [('https://satcompetition.github.io/2026/downloads/track_main_2026.uri',ARCHIVES/'satcomp2026.uri'),
              ('https://benchmark-database.de/?track=main_2026',ARCHIVES/'gbd2026.html')]
    records=[]
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs={pool.submit(fetch,url,path):(url,path) for url,path in tasks}
        for future in as_completed(jobs):
            result=future.result(); records.append(result); print('Fetched '+result['path'],flush=True)
    # Table row provenance from GBD. Unknown statuses remain unknown.
    page=(ARCHIVES/'gbd2026.html').read_text(encoding='utf-8')
    rows=[]
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',page,re.S):
        cells=re.findall(r'<td[^>]*>(.*?)</td>',tr,re.S)
        if not cells: continue
        clean=[re.sub('<[^>]+>','',c).strip() for c in cells]
        match=re.search(r'/file/([0-9a-f]{32})',tr)
        if match: rows.append(dict(hash=match.group(1),cells=clean))
    (ROOT/'sources'/'satcomp2026-table.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    # HEAD the first 220 deterministic entries and select 120 small enough originals.
    def head(row):
        url=f'https://benchmark-database.de/file/{row["hash"]}?context=cnf'
        try:
            with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=25) as response:
                return int(response.headers.get('Content-Length','999999999')),row,url
        except Exception: return 999999999,row,url
    with ThreadPoolExecutor(max_workers=10) as pool:
        sizes=list(pool.map(head,rows))
    chosen=sorted((x for x in sizes if x[0]<=2_000_000),key=lambda x:(x[0],x[1]['hash']))[:120]
    print(f'SAT Competition: selected {len(chosen)} / {len(rows)} source files',flush=True)
    selected=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs={pool.submit(fetch,url,ROOT/'sources'/'originals'/'satcomp2026'/f'{row["hash"]}.cnf.xz'):(size,row,url) for size,row,url in chosen}
        for future in as_completed(jobs):
            record=future.result(); record['gbd']=jobs[future][1]; selected.append(record)
    (ROOT/'sources'/'satcomp2026-selection.json').write_text(json.dumps(sorted(selected,key=lambda x:x['path']),indent=2)+'\n',encoding='utf-8')
    (ROOT/'sources'/'satlib-downloads.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')


def archived_sat():
    url='https://zenodo.org/records/15125952/files/sc02to24.zip?download=1'
    mapping={line.split(maxsplit=1)[1]:line.split()[0] for line in (ARCHIVES/'satcomp02to24-gbd-map.txt').read_text().splitlines()}
    current={r['hash']:r for r in json.loads((ROOT/'sources'/'satcomp2026-table.json').read_text())}
    records=[]
    with ZipFile(RemoteZip(url)) as archive:
        infos=sorted((x for x in archive.infolist() if not x.is_dir() and x.file_size<=1_000_000),key=lambda x:(x.file_size,x.filename))
        selected=[x for x in infos if mapping.get(x.filename) in current][:40]
        families=set()
        for info in infos:
            if len(selected)>=120: break
            family=re.split(r'[-_\d.]',info.filename)[0].lower()
            if family not in families and info not in selected:
                selected.append(info); families.add(family)
        for info in infos:
            if len(selected)>=120: break
            if info not in selected: selected.append(info)
        for index,info in enumerate(selected):
            destination=ROOT/'sources'/'originals'/'satcompetition_archive'/info.filename
            destination.parent.mkdir(parents=True,exist_ok=True)
            if not destination.exists(): destination.write_bytes(archive.read(info))
            key=mapping.get(info.filename)
            records.append(dict(url=url,archive_member=info.filename,path=destination.relative_to(ROOT).as_posix(),gbd_hash=key,gbd=current.get(key),also_in_main_2026=key in current))
            if index%10==0: print(f'Archived SAT Competition: {index+1}/{len(selected)}',flush=True)
    (ROOT/'sources'/'satcompetition-archive-selection.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('phase',choices=['mse','sat','archived-sat']); args=ap.parse_args()
    if args.phase=='mse': mse()
    elif args.phase=='sat': sat_sources()
    else: archived_sat()
