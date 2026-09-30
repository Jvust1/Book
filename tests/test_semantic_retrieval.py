import unittest

from runtime.semantic_retrieval import SentenceTransformerSemanticIndex


class FakeModel:
    def encode(self, texts, **kwargs):
        rows = []
        for text in texts:
            if "泛函" in text or "Banach" in text:
                rows.append([1.0, 0.0])
            elif "货币" in text:
                rows.append([0.0, 1.0])
            else:
                rows.append([0.5, 0.5])
        return rows


class SemanticRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.index = SentenceTransformerSemanticIndex(FakeModel())
        self.index.build([
            {
                "document_id": "fa-1",
                "text": "泛函分析中的 Banach 空间与完备性",
                "metadata": {"course": "functional-analysis"},
            },
            {
                "document_id": "money-1",
                "text": "货币供给与中央银行资产负债表",
                "metadata": {"course": "money-finance"},
            },
        ])

    def test_semantic_query_ranks_related_chunk_first(self):
        hits = self.index.query("Banach 空间是什么", limit=2)
        self.assertEqual(hits[0].document_id, "fa-1")
        self.assertGreater(hits[0].score, hits[1].score)

    def test_query_preserves_metadata(self):
        hit = self.index.query("货币政策", limit=1)[0]
        self.assertEqual(hit.document_id, "money-1")
        self.assertEqual(hit.metadata["course"], "money-finance")

    def test_invalid_document_fails_closed(self):
        with self.assertRaises(ValueError):
            self.index.build([{"document_id": "", "text": "x"}])


if __name__ == "__main__":
    unittest.main()
