import unittest,fitz
from unittest.mock import patch
from audit_v5_glyphs import compare_pages,audit_document,lines_of

def doc(text='ABC',x=72,y=100,pages=1,width=595.27559):
 d=fitz.open()
 for _ in range(pages):
  p=d.new_page(width=width,height=841.88976)
  if text:p.insert_text((x,y),text,fontsize=12)
 return d

class GlyphAuditTests(unittest.TestCase):
 def test_identical(self):
  a=doc();b=doc();r=compare_pages(a[0],b[0]);self.assertEqual(r['removed_position_glyphs'],0);self.assertEqual(r['added_position_glyphs'],0)
 def test_deletion(self):
  a=doc();b=doc('AB');r=compare_pages(a[0],b[0]);self.assertEqual(r['removed_position_glyphs'],1);self.assertEqual(r['changes'][0]['removed'],'C')
 def test_insertion(self):
  a=doc('AB');b=doc();self.assertEqual(compare_pages(a[0],b[0])['added_position_glyphs'],1)
 def test_duplicate_counter(self):
  a=doc('A');b=doc('A');line=lines_of(a[0])[0]
  with patch('audit_v5_glyphs.lines_of',side_effect=[[line,line],[line]]):
   self.assertEqual(compare_pages(a[0],b[0])['removed_position_glyphs'],1)
 def test_rounding_tolerance(self):
  a=doc();b=doc(x=72.03);r=compare_pages(a[0],b[0]);self.assertEqual(r['removed_position_glyphs'],0);self.assertEqual(r['position_tolerance_matches'],3)
 def test_real_shift_not_ignored(self):
  a=doc();b=doc(x=73);r=compare_pages(a[0],b[0]);self.assertEqual(r['removed_position_glyphs'],3);self.assertEqual(r['added_position_glyphs'],3)
 def test_page_count_fail(self):
  a=doc();b=doc(pages=2)
  with self.assertRaises(ValueError):audit_document(a.tobytes(),b.tobytes(),'synthetic')
 def test_geometry_reported_not_equivalence(self):
  a=doc();b=doc(width=600);r=audit_document(a.tobytes(),b.tobytes(),'synthetic');self.assertFalse(r['geometry_equal']);self.assertEqual(r['content_equivalence'],'NOT_ESTABLISHED')
 def test_whitespace_excluded(self):
  d=doc('A B');self.assertEqual(sum(len(x['chars']) for x in lines_of(d[0])),2)
 def test_margins_separate(self):
  a=doc('AB',y=20);b=doc('A',y=20);self.assertEqual(compare_pages(a[0],b[0])['changes'][0]['label'],'MARGIN_CHANGE')
if __name__=='__main__':unittest.main()
