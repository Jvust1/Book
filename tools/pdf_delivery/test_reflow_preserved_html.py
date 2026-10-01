import unittest,tempfile,json,copy,base64
from pathlib import Path
import fitz
from reflow_preserved_html import preserved_blocks,asset_path,render_one,stylesheet,nonspace

class PreservedHTMLTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'document-assets').mkdir()
  (self.root/'document-assets/a.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9l8AAAAASUVORK5CYII='))
  self.doc={'schema':'book-reflow-document-v1','id':'demo','book_title':'Synthetic Book','title':'Example','mode':'practice','blocks':[{'id':'b1','kind':'paragraph','html':'<p>AI reference answer. <strong>Original time boundary.</strong></p>','reader_html':'<p>Answer.</p>','reader_visibility':'hidden'}]}
 def tearDown(self):self.tmp.cleanup()
 def test_original_not_reader_html(self):
  parts,meta=preserved_blocks(self.doc,self.root);self.assertIn('AI reference answer',''.join(parts));self.assertTrue(meta['source_html_text_unchanged'])
 def test_hidden_reader_preserved(self):
  parts,meta=preserved_blocks(self.doc,self.root);self.assertEqual(meta['block_count'],1);self.assertIn('time boundary',''.join(parts))
 def test_duplicate_ids_rejected(self):
  self.doc['blocks']*=2
  with self.assertRaises(ValueError):preserved_blocks(self.doc,self.root)
 def test_schema_rejected(self):
  self.doc['schema']='different'
  with self.assertRaises(ValueError):preserved_blocks(self.doc,self.root)
 def test_script_rejected(self):
  self.doc['blocks'][0]['html']='<script>alert(1)</script>'
  with self.assertRaises(ValueError):preserved_blocks(self.doc,self.root)
 def test_event_attribute_rejected(self):
  self.doc['blocks'][0]['html']='<p onclick="bad()">safe</p>'
  with self.assertRaises(ValueError):preserved_blocks(self.doc,self.root)
 def test_missing_html_rejected(self):
  self.doc['blocks'][0].pop('html')
  with self.assertRaises(ValueError):preserved_blocks(self.doc,self.root)
 def test_text_and_order_preserved(self):
  self.doc['blocks']=[{'id':'a','html':'<p>A &amp; B<br>C</p>'},{'id':'b','html':'<p>D</p>'}];parts,m=preserved_blocks(self.doc,self.root);self.assertEqual(nonspace(m['plain']),'A&BCD');self.assertEqual(m['block_ids'],['a','b'])
 def test_safe_asset(self):self.assertEqual(asset_path('/document-assets/a.png',self.root),self.root/'document-assets/a.png')
 def test_network_rejected(self):
  with self.assertRaises(ValueError):asset_path('https://example.org/a.png',self.root)
 def test_traversal_rejected(self):
  with self.assertRaises(ValueError):asset_path('document-assets/%2e%2e/private.png',self.root)
 def test_foreign_root_rejected(self):
  with self.assertRaises(ValueError):asset_path('/etc/passwd',self.root)
 def test_missing_asset_rejected(self):
  with self.assertRaises(FileNotFoundError):asset_path('document-assets/missing.png',self.root)
 def test_query_rejected(self):
  with self.assertRaises(ValueError):asset_path('document-assets/a.png?secret=1',self.root)
 def test_size_range(self):
  with self.assertRaises(ValueError):stylesheet(11,'test')
 def test_render_actual_a4_and_size(self):
  p=self.root/'source.json';p.write_text(json.dumps(self.doc));out=self.root/'build/one.pdf';r=render_one(p,self.root,out,out.with_suffix('.html'),12)
  with fitz.open(out) as d:
   self.assertAlmostEqual(d[0].rect.width,595.27559,places=2);self.assertIn('AI reference answer',d[0].get_text());self.assertFalse(r['academic_acceptance'])
   sizes=[s['size'] for b in d[0].get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for s in l['spans'] if 'AI reference answer' in s['text']]
   self.assertTrue(any(abs(s-9)<.01 for s in sizes))
 def test_output_overwrite_source_rejected(self):
  p=self.root/'source.json';p.write_text(json.dumps(self.doc))
  with self.assertRaises(ValueError):render_one(p,self.root,p,self.root/'out.html',12)
 def test_existing_output_rejected(self):
  p=self.root/'source.json';p.write_text(json.dumps(self.doc));o=self.root/'out.pdf';o.touch()
  with self.assertRaises(FileExistsError):render_one(p,self.root,o,o.with_suffix('.html'),12)
 def test_table_spans_rejected(self):
  self.doc['blocks'][0]['html']='<table><tr><td colspan="999">x</td></tr></table>'
  with self.assertRaises(ValueError):preserved_blocks(self.doc,self.root)
if __name__=='__main__':unittest.main()
