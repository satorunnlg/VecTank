# tests/test_table.py
import unittest
import numpy as np
from vectank.table import VectorTable
from vectank.core import VectorSimMethod

class TestVectorTable(unittest.TestCase):
    def setUp(self):
        self.table = VectorTable("test", 5, VectorSimMethod.COSINE, np.float32)

    def test_add_and_search_vector(self):
        vector = np.array([1, 2, 3, 4, 5], dtype=np.float32)
        key = self.table.add_vector(vector, {"test": "data"})
        self.assertIsInstance(key, str)
        query = np.array([1, 2, 3, 4, 5], dtype=np.float32)
        results = self.table.search(query, top_k=1)
        self.assertEqual(len(results), 1)

if __name__ == '__main__':
    unittest.main()
