#!/usr/bin/env python3
"""Rebuild a supported local JSON/HTML collection; never changes its sources."""
from __future__ import annotations
import argparse,concurrent.futures,json,re,hashlib
import fitz
from pathlib import Path
from reflow_preserved_html import render_one

def job(args):
    document,asset_root,output_root,px=args
    doc=json.loads(document.read_text(encoding='utf-8'));identifier=doc['id']
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',identifier):raise ValueError('Unsafe document id')
    folder=output_root/f'{px}px';return render_one(document,asset_root,folder/f'{identifier}_{px}px.pdf',folder/f'{identifier}_{px}px.html',px)

def merge_outputs(rows: list[dict], output_root: Path) -> list[dict]:
    if len({r['book_title'] for r in rows}) != 1:
        raise ValueError('One source book per merged collection is required')
    merged=[]
    for mode,px in sorted({(r['mode'],r['px']) for r in rows}):
        chosen=sorted([r for r in rows if r['mode']==mode and r['px']==px],key=lambda r:r['id'])
        target=output_root/f'collection_{mode}_{px}px.pdf'
        if target.exists():raise FileExistsError(target)
        with fitz.open() as out:
            toc=[]
            for r in chosen:
                with fitz.open(r['pdf']) as doc:
                    toc.append([1,r['title'],len(out)+1]);out.insert_pdf(doc)
            out.set_toc(toc);out.set_metadata({'title':f"{chosen[0]['book_title']} {mode} {px}px source-preserving candidate",'subject':'Not academic acceptance; inherited source defects remain.'})
            out.save(target,garbage=4,deflate=True)
            merged.append({'mode':mode,'px':px,'pdf':str(target),'pages':len(out),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    return merged

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_root',type=Path,help='Root containing documents/ and document-assets/')
    p.add_argument('output_root',type=Path,help='New directory, not a previously built output')
    p.add_argument('--combine',action='store_true');p.add_argument('--pattern',default='*.json');p.add_argument('--sizes',nargs='+',type=int,default=[10,12,15],choices=[10,12,15]);p.add_argument('--jobs',type=int,default=2)
    a=p.parse_args()
    if a.output_root.exists():raise FileExistsError('Use a new output directory')
    docs=sorted((a.source_root/'documents').glob(a.pattern))
    if not docs:raise ValueError('No source documents')
    if not 1<=a.jobs<=8:raise ValueError('jobs must be 1..8')
    ids=[json.loads(d.read_text(encoding='utf-8'))['id'] for d in docs]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate source document id')
    a.output_root.mkdir(parents=True)
    args=[(d,a.source_root.resolve(),a.output_root.resolve(),px) for d in docs for px in a.sizes]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.jobs) as pool:results=list(pool.map(job,args))
    merged=merge_outputs(results,a.output_root) if a.combine else []
    (a.output_root/'build_manifest.json').write_text(json.dumps({'results':results,'merged':merged,'academic_acceptance':False},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Built {len(results)} PDFs. Layout candidates only; source content is not academically approved.')
if __name__=='__main__':main()
