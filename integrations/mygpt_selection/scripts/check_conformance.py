"""Compare independent JS/Python projections of every pinned r6 candidate.

This checks identity, not mathematics. Headings with empty bodies are expected
rejections, not skipped tests. No source text is retained in the summary.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from book_mygpt_selection.contract import BridgeError, FileReader, Selection, digest, project
from book_mygpt_selection.host import verify_source


def run(root: Path) -> dict:
    expected,identity=verify_source(root)
    reader=FileReader(root,expected_files=expected)
    with tempfile.TemporaryDirectory(prefix='book-projection-') as tmp:
        vectors=Path(tmp)/'vectors.json'
        subprocess.run(['node',str(Path(__file__).with_name('project_vectors.cjs')),str(root),str(vectors)],check=True,timeout=90)
        raw=vectors.read_bytes();assert len(raw)<16777216
        rows=json.loads(raw)
    cache={};counts=Counter();mismatches=[]
    for row in rows:
        value=row['selection'];key=(value['course_id'],value['section_id'])
        if key not in cache:cache[key]=reader.snapshot(*key)
        try:actual={'hash':digest(project(*cache[key],Selection.parse(value)))}
        except BridgeError as exc:actual={'error':exc.code}
        wanted={k:v for k,v in row.items() if k!='selection'}
        if actual!=wanted:mismatches.append({'selection':value,'python':actual,'javascript':wanted})
        counts[(value['layer'],value['representation'],actual.get('error','accepted'))]+=1
    return {'schema':'book.projection-conformance.v1','identity':identity,'vectors':len(rows),'sections':len(cache),
            'mismatches':mismatches,'vector_file_sha256':hashlib.sha256(raw).hexdigest(),
            'counts':[dict(layer=k[0],representation=k[1],result=k[2],count=v) for k,v in sorted(counts.items())],
            'scope':'Exact JS/Python body projection identity, not mathematical correctness',
            'accepted':bool(rows) and not mismatches}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--r6-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=run(a.r6_root)
    with a.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ['accepted','vectors','sections','mismatches']}));raise SystemExit(0 if result['accepted'] else 1)
