# tests/test_db.py
import unittest
from vectank.db import VectorDB
from vectank.core import VectorSimMethod
import numpy as np

class TestVectorDB(unittest.TestCase):
    def setUp(self):
        self.db = VectorDB()

    def test_create_and_get_table(self):
        table = self.db.create_table("test_table", 3, VectorSimMethod.COSINE, np.float32)
        self.assertIsNotNone(table)
        self.assertEqual(self.db.get_table("test_table"), table)

if __name__ == '__main__':
    unittest.main()
