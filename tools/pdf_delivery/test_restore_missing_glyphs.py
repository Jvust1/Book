import unittest,tempfile,hashlib,copy
from pathlib import Path
import fitz
from audit_v5_glyphs import lines_of,compare_pages
from restore_missing_glyphs import restore

class RestoreGlyphTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);a=fitz.open();p=a.new_page();p.insert_text((72,100),'ABC',fontsize=12);chars=[c for l in lines_of(p) for c in l['chars']];self.char=chars[-1];self.a=self.root/'source.pdf';a.save(self.a)
  b=fitz.open(self.a);r=fitz.Rect(self.char['bbox']);r.x0+=.2;r.x1-=.2;b[0].add_redact_annot(r,fill=None);b[0].apply_redactions(images=0,graphics=0);self.b=self.root/'v5.pdf';b.save(self.b)
  self.spec={'id':'synthetic','source_sha256':hashlib.sha256(self.a.read_bytes()).hexdigest(),'v5_sha256':hashlib.sha256(self.b.read_bytes()).hexdigest(),'patches':[{'page':1,'glyphs':[self.char]}]};self.out=self.root/'new.pdf'
 def tearDown(self):self.tmp.cleanup()
 def test_restores_one_only(self):
  r=restore(self.a,self.b,self.out,self.spec);self.assertEqual(r['restored_glyphs'],1)
  with fitz.open(self.b) as a,fitz.open(self.out) as b:
   diff=compare_pages(a[0],b[0]);self.assertEqual(diff['added_position_glyphs'],1);self.assertEqual(diff['removed_position_glyphs'],0)
 def test_original_unchanged(self):
  aa=self.a.read_bytes();bb=self.b.read_bytes();restore(self.a,self.b,self.out,self.spec);self.assertEqual(self.a.read_bytes(),aa);self.assertEqual(self.b.read_bytes(),bb)
 def test_bad_source_hash(self):
  self.spec['source_sha256']='0'*64
  with self.assertRaises(ValueError):restore(self.a,self.b,self.out,self.spec)
 def test_bad_v5_hash(self):
  self.spec['v5_sha256']='0'*64
  with self.assertRaises(ValueError):restore(self.a,self.b,self.out,self.spec)
 def test_existing_glyph_rejected(self):
  self.spec['v5_sha256']=self.spec['source_sha256']
  with self.assertRaises(ValueError):restore(self.a,self.a,self.out,self.spec)
 def test_source_glyph_missing_rejected(self):
  self.spec['patches'][0]['glyphs'][0]['c']='Z'
  with self.assertRaises(ValueError):restore(self.a,self.b,self.out,self.spec)
 def test_input_output_rejected(self):
  with self.assertRaises(ValueError):restore(self.a,self.b,self.b,self.spec)
 def test_existing_output_rejected(self):
  self.out.write_bytes(b'keep')
  with self.assertRaises(FileExistsError):restore(self.a,self.b,self.out,self.spec)
  self.assertEqual(self.out.read_bytes(),b'keep')
 def test_duplicate_instruction_rejected(self):
  self.spec['patches'][0]['glyphs']*=2
  with self.assertRaises(ValueError):restore(self.a,self.b,self.out,self.spec)
 def test_bad_isolated_cid_rejected(self):
  self.spec['patches'][0]['glyphs'][0]['font_isolation']={'font_xref':5,'cid_hex':'not-a-cid'}
  with self.assertRaises(ValueError):restore(self.a,self.b,self.out,self.spec)
if __name__=='__main__':unittest.main()
