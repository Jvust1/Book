import hashlib, io, json, tempfile, unittest, zipfile
from pathlib import Path
from merge_raw_parts import merge_parts, safe_name

class MergeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name)
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr('test.txt','synthetic fixture')
        data=buf.getvalue();self.manifest={'original':{'name':'sample.zip','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()},'parts':[]}
        for i,start in enumerate(range(0,len(data),40)):
            part=data[start:start+40];name=f'sample.zip.part{i:02d}';(self.root/name).write_bytes(part)
            self.manifest['parts'].append({'name':name,'bytes':len(part),'sha256':hashlib.sha256(part).hexdigest()})
    def test_merge(self):self.assertTrue(merge_parts(self.root,self.manifest).is_file())
    def test_idempotent(self):self.assertEqual(merge_parts(self.root,self.manifest),merge_parts(self.root,self.manifest))
    def test_bin_suffix(self):
        p=self.root/self.manifest['parts'][0]['name'];p.rename(str(p)+'.bin');self.assertTrue(merge_parts(self.root,self.manifest).is_file())
    def test_ambiguous(self):
        p=self.root/self.manifest['parts'][0]['name'];Path(str(p)+'.bin').write_bytes(p.read_bytes())
        with self.assertRaises(ValueError):merge_parts(self.root,self.manifest)
    def test_corrupt(self):
        p=self.root/self.manifest['parts'][0]['name'];p.write_bytes(b'x'*p.stat().st_size)
        with self.assertRaises(ValueError):merge_parts(self.root,self.manifest)
    def test_missing(self):
        (self.root/self.manifest['parts'][0]['name']).unlink()
        with self.assertRaises(ValueError):merge_parts(self.root,self.manifest)
    def test_existing_wrong(self):
        (self.root/'sample.zip').write_bytes(b'keep me')
        with self.assertRaises(ValueError):merge_parts(self.root,self.manifest)
        self.assertEqual((self.root/'sample.zip').read_bytes(),b'keep me')
    def test_order(self):
        self.manifest['parts'].reverse()
        with self.assertRaises(ValueError):merge_parts(self.root,self.manifest)
    def test_sum(self):
        self.manifest['original']['bytes']+=1
        with self.assertRaises(ValueError):merge_parts(self.root,self.manifest)
    def test_escape(self):
        for name in ('../bad','/bad','x\\y','C:x','..','', 'a\x00b'):
            with self.subTest(name=name), self.assertRaises(ValueError):safe_name(name)
if __name__=='__main__':unittest.main()
