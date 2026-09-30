import math
import unittest

from runtime.faiss_semantic_index import FaissSemanticIndex


class FakeModel:
    def encode(self, texts, **kwargs):
        rows = []
        for text in texts:
            if "Banach" in text or "泛函" in text:
                rows.append([1.0, 0.0])
            elif "货币" in text:
                rows.append([0.0, 1.0])
            else:
                rows.append([0.5, 0.5])
        return rows


class FakeIndex:
    def __init__(self, dimension):
        self.dimension = dimension
        self.rows = []

    def add(self, matrix):
        self.rows.extend([list(row) for row in matrix])

    def search(self, matrix, count):
        query = matrix[0]
        scored = []
        for idx, row in enumerate(self.rows):
            scored.append((sum(a * b for a, b in zip(query, row)), idx))
        scored.sort(reverse=True)
        selected = scored[:count]
        return [[score for score, _ in selected]], [[idx for _, idx in selected]]


class FakeFaiss:
    IndexFlatIP = FakeIndex

    @staticmethod
    def normalize_L2(matrix):
        for row in matrix:
            norm = math.sqrt(sum(value * value for value in row))
            if norm:
                for idx, value in enumerate(row):
                    row[idx] = value / norm


class FaissSemanticIndexTests(unittest.TestCase):
    def setUp(self):
        self.index = FaissSemanticIndex(
            FakeModel(),
            faiss_module=FakeFaiss,
            array_factory=lambda rows: [list(row) for row in rows],
        )
        self.index.build([
            {
                "document_id": "fa-1",
                "text": "泛函分析中的 Banach 空间",
                "metadata": {"course": "functional-analysis"},
            },
            {
                "document_id": "money-1",
                "text": "货币供给与中央银行",
                "metadata": {"course": "money-finance"},
            },
        ])

    def test_query_returns_faiss_ranked_semantic_hits(self):
        hits = self.index.query("Banach 空间", limit=2)
        self.assertEqual(hits[0].document_id, "fa-1")
        self.assertGreater(hits[0].score, hits[1].score)
        self.assertEqual(hits[0].metadata["course"], "functional-analysis")

    def test_empty_build_clears_index(self):
        self.index.build([])
        self.assertEqual(self.index.query("Banach"), [])

    def test_invalid_limit_fails_closed(self):
        with self.assertRaises(ValueError):
            self.index.query("Banach", limit=0)


if __name__ == "__main__":
    unittest.main()
