# tests/test_client.py
import unittest
from vectank.client import VectorDBClient
from vectank.core import VectorSimMethod
import numpy as np

class TestVectorDBClient(unittest.TestCase):
    def test_get_table(self):
        client = VectorDBClient()
        table = client.get_table("default")
        self.assertIsNotNone(table)

if __name__ == '__main__':
    unittest.main()
