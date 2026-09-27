#!/usr/bin/env python3
"""Restore learning r2 to a NEW directory from exact rc5 + a trusted delta ZIP."""
import argparse,hashlib,json,shutil,stat,tempfile,zipfile
from pathlib import Path,PurePosixPath

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def safe(s):
 if not isinstance(s,str) or not s or '\\' in s or ':' in s or PurePosixPath(s).is_absolute() or any(x in ('','.','..') for x in s.split('/')):raise ValueError('Unsafe path')
 return s
def restore(base,delta,out,expected):
 base=base.resolve();out=out.absolute()
 if out.exists() or out.is_symlink():raise ValueError('Output must be a new directory')
 if len(expected)!=64 or digest(delta)!=expected.lower():raise ValueError('Trusted delta SHA-256 mismatch')
 with zipfile.ZipFile(delta) as z:
  names=set();total=0
  for x in z.infolist():
   if x.is_dir():safe(x.filename.rstrip('/'));continue
   safe(x.filename)
   if x.filename in names or stat.S_ISLNK(x.external_attr>>16):raise ValueError('Duplicate or symlink')
   names.add(x.filename);total+=x.file_size
  if total>100*1024*1024:raise ValueError('Unexpected delta size')
  m=json.loads(z.read('learning-delta.json'))
  if m['schema']!='book-learning-delta-v1':raise ValueError('Wrong manifest')
  for name,h in m['baseline_files'].items():
   p=base/safe(name)
   if p.is_symlink() or not p.resolve().is_relative_to(base) or not p.is_file() or digest(p)!=h:raise ValueError('Wrong rc5 file: '+name)
  out.parent.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='book-learning-',dir=out.parent) as tmp:
   stage=Path(tmp)/'source';stage.mkdir()
   for name,entry in m['result_files'].items():
    name=safe(name);p=stage/name;p.parent.mkdir(parents=True,exist_ok=True)
    if 'payload/'+name in names:
     with z.open('payload/'+name) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst)
    else:shutil.copyfile(base/name,p)
    if p.stat().st_size!=entry['bytes'] or digest(p)!=entry['sha256']:raise ValueError('Result mismatch: '+name)
   if out.exists() or out.is_symlink():raise ValueError('Destination appeared')
   stage.rename(out)
 return {'verified_files':len(m['result_files']),'baseline_unchanged':True,'output':str(out)}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rc5-source',type=Path,required=True);p.add_argument('--delta',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:print(json.dumps(restore(a.rc5_source,a.delta,a.output,a.sha256),ensure_ascii=False))
 except (ValueError,OSError,KeyError,zipfile.BadZipFile) as e:p.exit(2,str(e)+'\n')
