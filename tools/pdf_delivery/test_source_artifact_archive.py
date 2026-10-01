"""Synthetic regression tests for evidence-bound retirement; no book content."""
import copy
import unittest
from apply_evidence_patch import patch_document, digest

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.doc={'id':'synthetic','blocks':[
            {'id':'a','html':'<p>Retained corrected prose.</p>','kind':'prose'},
            {'id':'b','html':'<h1>Header OCR 42</h1>','source':{'quality':'draft'},'reader_html':'legacy'},
            {'id':'c','html':'<p>Another paragraph.</p>','kind':'prose'}], 'anchor_aliases':{}}
        self.op={'op':'archive_source_artifact','block_id':'b','expected_html_sha256':digest(self.doc['blocks'][1]['html'].encode()),
                 'artifact_kind':'running_header','retained_by':['a'],'source_comparison':'Synthetic page margin, not body.',
                 'evidence_ids':['page-1'],'reason':'Explicit fixture comparison'}
    def patch(self):return patch_document(self.doc,[self.op],{'page-1'})
    def test_archive_exact_dictionary(self):
        out,_=self.patch();self.assertEqual(out['retired_source_artifacts'][0]['original_block'],self.doc['blocks'][1])
    def test_no_original_mutation(self):
        old=copy.deepcopy(self.doc);self.patch();self.assertEqual(old,self.doc)
    def test_preserve_other_blocks(self):self.assertEqual(self.patch()[0]['blocks'],[self.doc['blocks'][0],self.doc['blocks'][2]])
    def test_anchor_redirect(self):self.assertEqual(self.patch()[0]['anchor_aliases']['b'],'a')
    def test_no_semantic_claim(self):self.assertFalse(self.patch()[1][0]['automatic_semantic_equivalence_claimed'])
    def test_quality_preserved(self):self.assertEqual(self.patch()[0]['retired_source_artifacts'][0]['original_block']['source']['quality'],'draft')
    def test_wrong_hash(self):
        self.op['expected_html_sha256']='0'*64
        with self.assertRaises(ValueError):self.patch()
    def test_no_hash(self):
        del self.op['expected_html_sha256']
        with self.assertRaises(ValueError):self.patch()
    def test_unknown_category(self):
        self.op['artifact_kind']='all_bad_text'
        with self.assertRaises(ValueError):self.patch()
    def test_decorative_category(self):self.op['artifact_kind']='decorative_ocr';self.assertEqual(len(self.patch()[0]['blocks']),2)
    def test_overlap_category(self):self.op['artifact_kind']='overlapping_transcription';self.assertEqual(len(self.patch()[0]['blocks']),2)
    def test_no_comparison(self):
        del self.op['source_comparison']
        with self.assertRaises(ValueError):self.patch()
    def test_blank_comparison(self):
        self.op['source_comparison']='  '
        with self.assertRaises(ValueError):self.patch()
    def test_no_reason(self):
        self.op['reason']=''
        with self.assertRaises(ValueError):self.patch()
    def test_unknown_evidence(self):
        self.op['evidence_ids']=['absent']
        with self.assertRaises(ValueError):self.patch()
    def test_missing_evidence(self):
        self.op['evidence_ids']=[]
        with self.assertRaises(ValueError):self.patch()
    def test_absent_retained(self):
        self.op['retained_by']=['missing']
        with self.assertRaises(ValueError):self.patch()
    def test_self_retained(self):
        self.op['retained_by']=['b']
        with self.assertRaises(ValueError):self.patch()
    def test_empty_retained(self):
        self.op['retained_by']=[]
        with self.assertRaises(ValueError):self.patch()
    def test_duplicate_retained(self):
        self.op['retained_by']=['a','a']
        with self.assertRaises(ValueError):self.patch()
    def test_string_retained(self):
        self.op['retained_by']='a'
        with self.assertRaises(ValueError):self.patch()
    def test_alias_conflict(self):
        self.doc['anchor_aliases']['b']='c'
        with self.assertRaises(ValueError):self.patch()
    def test_alias_wrong_type(self):
        self.doc['anchor_aliases']=[]
        with self.assertRaises(ValueError):self.patch()
    def test_existing_archive_kept(self):
        self.doc['retired_source_artifacts']=[{'previous':'entry'}];self.assertEqual(self.patch()[0]['retired_source_artifacts'][0],{'previous':'entry'})
    def test_target_retired_later_rejected(self):
        later=copy.deepcopy(self.op);later.update(block_id='a',retained_by=['c'],expected_html_sha256=digest(self.doc['blocks'][0]['html'].encode()))
        with self.assertRaises(ValueError):patch_document(self.doc,[self.op,later],{'page-1'})
    def test_multiple_retained(self):
        self.op['retained_by']=['a','c'];self.assertEqual(self.patch()[1][0]['retained_by'],['a','c'])

if __name__=='__main__':unittest.main()
