import unittest,tempfile
from pathlib import Path
import fitz
from build_preserved_collection import merge_outputs

class CollectionMergeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.rows=[]
  for i in (1,2):
   d=fitz.open();p=d.new_page();p.insert_text((72,72),f'chapter {i}');name=self.root/f'{i}.pdf';d.save(name)
   self.rows.append({'id':f'd-{i}','book_title':'Synthetic Book','title':f'Chapter {i}','mode':'learn','px':12,'pdf':str(name)})
 def tearDown(self):self.tmp.cleanup()
 def test_merge_pages_and_bookmarks(self):
  rows=merge_outputs(self.rows,self.root);self.assertEqual(rows[0]['pages'],2)
  with fitz.open(rows[0]['pdf']) as d:self.assertEqual(len(d.get_toc()),2);self.assertIn('chapter 2',d[1].get_text())
 def test_mixed_books_rejected(self):
  self.rows[1]['book_title']='Other'
  with self.assertRaises(ValueError):merge_outputs(self.rows,self.root)
 def test_no_overwrite(self):
  merge_outputs(self.rows,self.root)
  with self.assertRaises(FileExistsError):merge_outputs(self.rows,self.root)
if __name__=='__main__':unittest.main()
