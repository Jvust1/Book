"""Synthetic tests only; no private textbook text in test fixtures."""
import unittest
from build_source_registry import archive_path, candidate_key, image_sources, sha

class RegistryTests(unittest.TestCase):
    def test_absolute_local(self): self.assertEqual(archive_path('/document-assets/a.svg'), 'document-assets/a.svg')
    def test_relative_local(self): self.assertEqual(archive_path('documents/a.json'), 'documents/a.json')
    def test_percent_decode(self): self.assertEqual(archive_path('/a%20b/c.svg'), 'a b/c.svg')
    def test_traversal(self):
        for path in ('../a', '/a/../b', '/a/%2e%2e/b', '/a/./b'):
            with self.subTest(path=path), self.assertRaises(ValueError): archive_path(path)
    def test_external(self):
        for path in ('https://evil/a', '//evil/a', 'data:image/png;base64,AAA', 'file:///a'):
            with self.subTest(path=path), self.assertRaises(ValueError): archive_path(path)
    def test_ambiguous(self):
        for path in ('', '/', '/a//b', '/a\\b', '/a%5cb', '/a%00b', 'C:/a', '/a?x=1', '/a#b'):
            with self.subTest(path=path), self.assertRaises(ValueError): archive_path(path)
    def test_learning_candidate(self): self.assertEqual(candidate_key('fe', '学习/04_标题_学习_v5.pdf'), ('fe',4,'learn'))
    def test_zero_chapter(self): self.assertEqual(candidate_key('pf', '预习/00_绪论_预习_v5.pdf'), ('pf',0,'preview'))
    def test_review(self): self.assertEqual(candidate_key('fa', '复习/03_章_复习_v5.pdf'), ('fa',3,'review'))
    def test_practice(self): self.assertEqual(candidate_key('pde', '刷题/07_章_刷题_v5.pdf'), ('pde',7,'practice'))
    def test_combined_excluded(self):
        for name in ('章节合订/04_章节合订_v5.pdf', '全书合订版_v5.pdf', '学习/标题.pdf'):
            self.assertIsNone(candidate_key('fe',name))
    def test_unsupported_extensions(self): self.assertIsNone(candidate_key('fe','学习/04_学习.tex'))
    def test_not_nested(self): self.assertIsNone(candidate_key('fe','其他/学习/04_学习_v5.pdf'))
    def test_img_src_only(self): self.assertEqual(image_sources('<div><img src="/x.svg" alt="s"><a href="/y">x</a></div>'), ['/x.svg'])
    def test_reader_image_entities(self): self.assertEqual(image_sources("<IMG src='/a&amp;b.png'/>"), ['/a&b.png'])
    def test_empty_img(self): self.assertEqual(image_sources('<img alt="none"><img src="">'), [])
    def test_hash(self): self.assertEqual(sha(b'abc'), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')

if __name__ == '__main__': unittest.main()
