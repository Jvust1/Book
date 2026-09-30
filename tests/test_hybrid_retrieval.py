import unittest
from types import SimpleNamespace

from runtime.hybrid_retrieval import HybridSearch


class Keyword:
    def search(self, query, *, limit, section_id=None):
        return [
            SimpleNamespace(source_id="def-banach"),
            SimpleNamespace(source_id="example-norm"),
        ]


class Semantic:
    def query(self, query, *, limit):
        return [
            SimpleNamespace(document_id="example-norm"),
            SimpleNamespace(document_id="def-banach"),
        ]


class HybridRetrievalTests(unittest.TestCase):
    def test_rrf_rewards_items_found_by_both_retrievers(self):
        hits = HybridSearch(Keyword(), Semantic()).search("Banach", limit=2)
        self.assertEqual({h.source_id for h in hits}, {"def-banach", "example-norm"})
        self.assertTrue(all(h.keyword_rank is not None for h in hits))
        self.assertTrue(all(h.semantic_rank is not None for h in hits))

    def test_invalid_limit_fails_closed(self):
        with self.assertRaises(ValueError):
            HybridSearch(Keyword(), Semantic()).search("x", limit=0)


if __name__ == "__main__":
    unittest.main()
