# tests/test_store.py
import unittest
from vectank.store import VectorStore  # 旧 VectorDB → VectorStore に名称統一
from vectank.core import VectorSimMethod
import numpy as np

class TestVectorStore(unittest.TestCase):
    def setUp(self):
        """
        各テストケース実行前に、VectorStore インスタンスを初期化します。
        VectorStore は複数のタンク（旧テーブル）を管理するクラスです。
        """
        self.store = VectorStore()

    def test_create_and_get_tank(self):
        """
        create_tank() および get_tank() メソッドのテストです。
        ・"test_tank" という名前のタンクを作成し、戻り値が None ではないことを確認。
        ・get_tank() により、作成したタンクが正しく取得できるか検証します。
        """
        tank = self.store.create_tank("test_tank", 3, VectorSimMethod.COSINE, np.float32)
        self.assertIsNotNone(tank, "作成されたタンクは None であってはいけません。")
        self.assertEqual(self.store.get_tank("test_tank"), tank, "取得したタンクは作成したタンクと一致する必要があります。")
    
    def test_drop_tank_and_list_tanks(self):
        """
        drop_tank() および list_tanks() メソッドのテストです。
        ・複数のタンクを作成後、任意のタンクを削除し、タンク一覧（list_tanks()）に削除が反映されていることを確認します。
        """
        self.store.create_tank("tank1", 3, VectorSimMethod.COSINE, np.float32)
        self.store.create_tank("tank2", 3, VectorSimMethod.COSINE, np.float32)
        self.store.create_tank("tank3", 3, VectorSimMethod.COSINE, np.float32)
        
        tanks_before = self.store.list_tanks()
        self.assertIn("tank2", tanks_before, "tank2 は作成されたタンク一覧に含まれているはずです。")
        
        self.store.drop_tank("tank2")
        tanks_after = self.store.list_tanks()
        self.assertNotIn("tank2", tanks_after, "削除された tank2 はタンク一覧に含まれてはいけません。")
    
    def test_duplicate_tank_creation(self):
        """
        既存のタンク名と重複して create_tank() を呼び出した場合に
        ValueError が発生するか検証するテストです。
        """
        self.store.create_tank("duplicate", 3, VectorSimMethod.COSINE, np.float32)
        with self.assertRaises(ValueError):
            self.store.create_tank("duplicate", 3, VectorSimMethod.COSINE, np.float32)

if __name__ == '__main__':
    unittest.main()
