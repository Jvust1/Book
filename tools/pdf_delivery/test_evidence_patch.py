"""Synthetic tests; no textbook prose or scan bytes are distributed."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from apply_evidence_patch import digest, safe_child, patch_document, apply_patch

class BlockTests(unittest.TestCase):
    def setUp(self):
        self.doc={'id':'synthetic','schema':'book-reflow-document-v1','reader_html':'old','finalized':True,'blocks':[
            {'id':'a','html':'<p>alpha</p>','kind':'prose','reader_html':'old','source':{'quality':'draft'}},
            {'id':'b','html':'<p>beta</p>','kind':'prose'},
            {'id':'c','html':'<p>gamma</p>','kind':'prose'}]}
        self.rep={'op':'replace','block_id':'a','expected_html_sha256':digest(b'<p>alpha</p>'),'html':'<p>ALPHA</p>','kind':'heading','evidence_ids':['p1'],'reason':'synthetic approved correction'}
        self.ins={'op':'insert_after','after_block_id':'a','block':{'id':'new','html':'<p>new</p>'},'evidence_ids':['p1'],'reason':'synthetic split'}
        self.mov={'op':'move_after','block_id':'c','after_block_id':'a','evidence_ids':['p1'],'reason':'synthetic relocation'}
    def run_patch(self,ops):return patch_document(self.doc,ops,{'p1'})
    def test_original_not_mutated(self):
        before=copy.deepcopy(self.doc); self.run_patch([self.rep]); self.assertEqual(before,self.doc)
    def test_replacement(self):self.assertEqual(self.run_patch([self.rep])[0]['blocks'][0]['html'],'<p>ALPHA</p>')
    def test_old_reader_removed(self):self.assertNotIn('reader_html',self.run_patch([self.rep])[0]['blocks'][0])
    def test_quality_not_promoted(self):self.assertEqual(self.run_patch([self.rep])[0]['blocks'][0]['source']['quality'],'draft')
    def test_unaffected_exact(self):self.assertEqual(self.run_patch([self.rep])[0]['blocks'][1:],self.doc['blocks'][1:])
    def test_plain_reflects_new(self):self.assertEqual(self.run_patch([self.rep])[0]['blocks'][0]['plain'],'ALPHA')
    def test_log_hashes(self):self.assertEqual(self.run_patch([self.rep])[1][0]['after_html_sha256'],digest(b'<p>ALPHA</p>'))
    def test_wrong_html_identity(self):
        self.rep['expected_html_sha256']='0'*64
        with self.assertRaises(ValueError):self.run_patch([self.rep])
    def test_empty_replacement(self):
        self.rep['html']=' '
        with self.assertRaises(ValueError):self.run_patch([self.rep])
    def test_unknown_evidence(self):
        self.rep['evidence_ids']=['unknown']
        with self.assertRaises(ValueError):self.run_patch([self.rep])
    def test_no_evidence(self):
        self.rep['evidence_ids']=[]
        with self.assertRaises(ValueError):self.run_patch([self.rep])
    def test_duplicate_original_ids(self):
        self.doc['blocks'][1]['id']='a'
        with self.assertRaises(ValueError):self.run_patch([self.rep])
    def test_missing_original_ids(self):
        del self.doc['blocks'][1]['id']
        with self.assertRaises(ValueError):self.run_patch([self.rep])
    def test_insert(self):self.assertEqual([b['id'] for b in self.run_patch([self.ins])[0]['blocks']],['a','new','b','c'])
    def test_insert_duplicate(self):
        self.ins['block']['id']='b'
        with self.assertRaises(ValueError):self.run_patch([self.ins])
    def test_insert_empty(self):
        self.ins['block']['html']=''
        with self.assertRaises(ValueError):self.run_patch([self.ins])
    def test_move(self):self.assertEqual([b['id'] for b in self.run_patch([self.mov])[0]['blocks']],['a','c','b'])
    def test_move_same(self):
        self.mov['after_block_id']='c'
        with self.assertRaises(ValueError):self.run_patch([self.mov])
    def test_delete_not_supported(self):
        self.rep['op']='delete'
        with self.assertRaises(ValueError):self.run_patch([self.rep])
    def test_operation_order(self):self.assertEqual([b['id'] for b in self.run_patch([self.ins,self.mov])[0]['blocks']],['a','c','new','b'])
    def test_failure_leaves_original(self):
        before=copy.deepcopy(self.doc);bad=copy.deepcopy(self.rep);bad['block_id']='missing'
        with self.assertRaises(KeyError):self.run_patch([self.rep,bad])
        self.assertEqual(before,self.doc)

    def test_retire_keeps_archive(self):
        self.doc['blocks'][1]['html']='<p>alpha</p>'
        op={'op':'retire_duplicate','block_id':'b','duplicate_of_block_id':'a','expected_html_sha256':digest(b'<p>alpha</p>'),'evidence_ids':['p1'],'reason':'duplicate'}
        out,log=self.run_patch([op]);self.assertEqual([b['id'] for b in out['blocks']],['a','c']);self.assertEqual(out['retired_duplicate_blocks'][0]['original_block'],self.doc['blocks'][1]);self.assertTrue(log[0]['archived_original_block'])
    def test_retire_not_matching(self):
        op={'op':'retire_duplicate','block_id':'b','duplicate_of_block_id':'a','expected_html_sha256':digest(b'<p>beta</p>'),'evidence_ids':['p1'],'reason':'not duplicate'}
        with self.assertRaises(ValueError):self.run_patch([op])
    def test_retire_wrong_identity(self):
        self.doc['blocks'][1]['html']='<p>alpha</p>'
        op={'op':'retire_duplicate','block_id':'b','duplicate_of_block_id':'a','expected_html_sha256':'0'*64,'evidence_ids':['p1'],'reason':'duplicate'}
        with self.assertRaises(ValueError):self.run_patch([op])
    def test_retire_self(self):
        op={'op':'retire_duplicate','block_id':'a','duplicate_of_block_id':'a','evidence_ids':['p1'],'reason':'self'}
        with self.assertRaises(ValueError):self.run_patch([op])
    def test_retire_empty(self):
        self.doc['blocks'][1]['html']='<p> </p>'
        op={'op':'retire_duplicate','block_id':'b','duplicate_of_block_id':'a','expected_html_sha256':digest(b'<p> </p>'),'evidence_ids':['p1'],'reason':'empty'}
        with self.assertRaises(ValueError):self.run_patch([op])

class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.src=self.root/'src';self.src.mkdir();(self.src/'documents').mkdir()
        self.doc={'id':'synthetic','blocks':[{'id':'a','html':'<p>alpha</p>'}],'reader_html':'old','finalized':True}
        self.raw=json.dumps(self.doc).encode();(self.src/'documents/a.json').write_bytes(self.raw)
        self.scan=self.root/'scan.pdf';self.scan.write_bytes(b'synthetic identity fixture, not an actual scan')
        op={'op':'replace','block_id':'a','expected_html_sha256':digest(b'<p>alpha</p>'),'html':'<p>ALPHA</p>','evidence_ids':['p1'],'reason':'test'}
        self.spec={'schema':'book-evidence-patch-v1','revision':'synthetic-v1','source_scan_sha256':digest(self.scan.read_bytes()),'evidence_ids':['p1'],'documents':[{'file':'documents/a.json','document_id':'synthetic','expected_json_sha256':digest(self.raw),'review_scope':'test only','operations':[op]}]}
        self.specfile=self.root/'spec.json';self.dest=self.root/'new'
    def apply(self):
        self.specfile.write_text(json.dumps(self.spec));return apply_patch(self.src,self.scan,self.specfile,self.dest)
    def test_frozen_original_and_updated(self):
        self.apply();self.assertEqual((self.dest/'source_original/documents/a.json').read_bytes(),self.raw);self.assertEqual((self.src/'documents/a.json').read_bytes(),self.raw)
    def test_approval_not_implied(self):
        self.apply();new=json.loads((self.dest/'source/documents/a.json').read_text());self.assertFalse(new['finalized']);self.assertFalse(new['academic_review']['full_academic_acceptance']);self.assertNotIn('reader_html',new)
    def test_wrong_scan(self):
        self.spec['source_scan_sha256']='0'*64
        with self.assertRaises(ValueError):self.apply()
        self.assertFalse(self.dest.exists())
    def test_wrong_document_hash(self):
        self.spec['documents'][0]['expected_json_sha256']='0'*64
        with self.assertRaises(ValueError):self.apply()
    def test_wrong_document_id(self):
        self.spec['documents'][0]['document_id']='different'
        with self.assertRaises(ValueError):self.apply()
    def test_existing_destination(self):
        self.dest.mkdir();(self.dest/'keep').write_text('keep')
        with self.assertRaises(FileExistsError):self.apply()
        self.assertEqual((self.dest/'keep').read_text(),'keep')
    def test_destination_under_source(self):
        self.dest=self.src/'new'
        with self.assertRaises(ValueError):self.apply()
    def test_duplicate_document(self):
        self.spec['documents']*=2
        with self.assertRaises(ValueError):self.apply()
    def test_duplicate_evidence(self):
        self.spec['evidence_ids']*=2
        with self.assertRaises(ValueError):self.apply()
    def test_schema(self):
        self.spec['schema']='other'
        with self.assertRaises(ValueError):self.apply()
    def test_path_traversal(self):
        self.spec['documents'][0]['file']='../escape'
        with self.assertRaises(ValueError):self.apply()
    def test_absolute_path(self):
        with self.assertRaises(ValueError):safe_child(self.src,'/tmp/x')
    def test_symlink_escape(self):
        (self.src/'linked').symlink_to(self.root/'elsewhere')
        with self.assertRaises(ValueError):safe_child(self.src,'linked')
    def test_asset_copy(self):
        (self.src/'document-assets').mkdir();(self.src/'document-assets/a.png').write_bytes(b'bytes');self.apply()
        self.assertEqual((self.dest/'source/document-assets/a.png').read_bytes(),b'bytes')
    def test_asset_symlink_rolls_back(self):
        (self.src/'document-assets').mkdir();(self.src/'document-assets/a').symlink_to(self.scan)
        with self.assertRaises(ValueError):self.apply()
        self.assertFalse(self.dest.exists());self.assertFalse(list(self.root.glob('.evidence-patch-*')))

class RenderProfileTests(unittest.TestCase):
    def test_legacy_profile(self):
        from reflow_preserved_html import stylesheet
        self.assertIn('v8r2',stylesheet(12,'test'));self.assertNotIn('.kind-table td > span',stylesheet(12,'test'))
    def test_new_edition_and_no_font_shrink(self):
        from reflow_preserved_html import stylesheet
        css=stylesheet(15,'test','v9',True);self.assertIn('v9',css);self.assertIn('font-size:15px',css);self.assertIn('white-space:nowrap',css);self.assertNotIn('transform:',css)
    def test_invalid_edition(self):
        from reflow_preserved_html import stylesheet
        for ed in ['bad";content:', 'a\nb', '', 'x'*25]:
            with self.subTest(ed=ed),self.assertRaises(ValueError):stylesheet(12,'test',ed)
    def test_invalid_size(self):
        from reflow_preserved_html import stylesheet
        with self.assertRaises(ValueError):stylesheet(9,'test','v9')

if __name__=='__main__':unittest.main()
