"""Deterministic contract/source checks. Does not certify mathematical proofs."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build_learning,build_teaching
DATA=ROOT/'web/data';CAT=json.loads((DATA/'catalog.json').read_text())
class Content(unittest.TestCase):
 def test_every_directory_and_category_resolves(self):
  total=0
  for m in CAT['books']:
   b=json.loads((DATA/(m['id']+'.json')).read_text());d=json.loads((DATA/(m['id']+'.learning.json')).read_text());by={r['id']:r for r in b['records']}
   self.assertEqual([s['id'] for s in d['sections']],[s['id'] for s in b['sections']]);total+=len(d['sections'])
   self.assertEqual(set(s['id'] for s in d['sections']),set(i for c in d['chapters'] for i in c['section_ids']))
   for s in d['sections']:
    for ids in s['categories'].values():
     for rid in ids:self.assertIn(rid,by);self.assertIsNot(by[rid].get('body_visible'),False)
  self.assertEqual(total,845)
 def test_deterministic_build_and_identity(self):
  for m in CAT['books']:
   d=json.loads((DATA/(m['id']+'.learning.json')).read_text());self.assertEqual(d,build_learning.compile_book(m));self.assertEqual(d['source_book_sha256'],hashlib.sha256((DATA/(m['id']+'.json')).read_bytes()).hexdigest())
 def test_teaching_contracts(self):
  units=problems=points=0
  for m in CAT['books']:
   d=json.loads((DATA/(m['id']+'.teaching.json')).read_text());self.assertEqual(d,build_teaching.compile_book(m));units+=len(d['units']);problems+=len(d['solved'])
   for u in d['units']:
    self.assertGreaterEqual(len(u['preview']['overview']),100,u['id']);self.assertGreaterEqual(len(u['review']['points']),3);self.assertGreaterEqual(len(u['review']['method']),3);self.assertGreaterEqual(len(u['review']['pitfalls']),2);points+=len(u['review']['points'])
   for q in d['solved']:self.assertGreaterEqual(len(q['steps']),2);self.assertTrue(q['answer']);self.assertFalse(q['independent_expert_review'])
  self.assertEqual((units,problems,points),(42,76,128))
 def test_original_answers_and_methods(self):
  count=0
  for m in CAT['books']:
   b=json.loads((DATA/(m['id']+'.json')).read_text());by={r['id']:r for r in b['records']};d=json.loads((DATA/(m['id']+'.learning.json')).read_text());qs={q['id']:q for q in json.loads((DATA/(m['id']+'.study.json')).read_text())['questions']}
   for qid,w in d['original_answers'].items():
    count+=1;self.assertIn(qid,qs);self.assertGreaterEqual(len(w['method']),3);self.assertGreaterEqual(len(w['steps']),2);self.assertFalse(w['textbook_official_solution']);self.assertFalse(w['independent_expert_review'])
    self.assertEqual([r['record_id'] for r in w['source_refs']],qs[qid]['record_ids'])
    for ref in w['source_refs']:self.assertEqual(ref['pdf_pages'],by[ref['record_id']].get('source_pdf_pages',[]))
    for rid in w.get('support_record_ids',[]):self.assertIn(rid,by)
  self.assertEqual(count,10)
 def test_no_frequency_or_whole_book_claim(self):
  for m in CAT['books']:
   d=json.loads((DATA/(m['id']+'.learning.json')).read_text());self.assertFalse(d['coverage']['whole_book_authored_complete']);self.assertEqual(d['coverage']['exam_frequency_evidence_count'],0)
 def test_explicit_chapter_id_parsing(self):
  for rid,c in [('ex_ch2_7_8','ch02'),('formula_ch8_32_R_Rstar_duality','ch08'),('ch01_prob_04','ch01'),('unknown-pdf123','unmapped')]:self.assertEqual(build_learning.chapter_for({'id':rid}),c)
  self.assertEqual(build_learning.chapter_for({'id':'p59','section_id':'2.6'}),'lecture-2')
 def test_new_numeric_examples(self):
  self.assertEqual(F(1,2)*F(1,10)**2/2,F(1,400));self.assertEqual(F(108,120),F(9,10));self.assertEqual(F(108,100),F(27,25))
 def test_script_order_and_single_boot(self):
  html=(ROOT/'web/index.html').read_text();names=['study-engine.js','exam-engine.js','app.js','study-ui.js','teaching-ui.js','learning-ui.js'];self.assertEqual(sorted(names,key=html.index),names)
  self.assertTrue((ROOT/'web/learning-ui.js').read_text().endswith('boot();\n'));self.assertFalse((ROOT/'web/teaching-ui.js').read_text().endswith('boot();\n'))
if __name__=='__main__':unittest.main(verbosity=2)
