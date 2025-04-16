# tests/test_store.py
import unittest
import tempfile
import os
from vectank.store import VectorStore
from vectank.core import VectorSimMethod
import numpy as np

class TestVectorStore(unittest.TestCase):
    def setUp(self):
        """
        各テストケース実行前に、VectorStore インスタンスを初期化します。
        VectorStore は複数のタンクを管理するクラスです。
        """
        self.store = VectorStore()
        # 内部の tanks 辞書をクリア
        self.store.tanks = {}

    def test_create_and_get_tank(self):
        """
        create_tank() および get_tank() メソッドのテストです。
        """
        tank = self.store.create_tank("test_tank", 3, VectorSimMethod.COSINE, np.float32)
        self.assertIsNotNone(tank, "作成されたタンクは None であってはいけません。")
        self.assertEqual(self.store.get_tank("test_tank"), tank, "取得したタンクは作成したタンクと一致する必要があります。")
        # persist が指定されていなければ False となり、永続化パスは None になるはず
        self.assertFalse(tank.persist, "永続化フラグが指定されていなければ False である必要があります。")
        self.assertIsNone(tank.persistence_path, "永続化パスは指定されなかった場合 None である必要があります。")

    def test_drop_tank_and_list_tanks(self):
        """
        drop_tank() および list_tanks() メソッドのテストです。
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
        ValueError が送出されるか検証するテストです。
        """
        self.store.create_tank("duplicate", 3, VectorSimMethod.COSINE, np.float32)
        with self.assertRaises(ValueError):
            self.store.create_tank("duplicate", 3, VectorSimMethod.COSINE, np.float32)

    def test_persistence_file_creation(self):
        """
        store_dir が指定された場合、永続化フラグ True のタンクで、
        タンク名に基づく永続化用ファイルが出力されることを検証します。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(store_dir=tmpdir)
            # persist=True でタンク作成
            tank = store.create_tank("persistent_tank", 3, VectorSimMethod.COSINE, np.float32, persist=True)
            expected_path = os.path.join(tmpdir, "persistent_tank")
            self.assertEqual(tank.persistence_path, expected_path, "永続化パスが正しく設定されていない")
            # save_to_file() を呼び出して、実際にファイル出力を実施
            tank.save_to_file()
            # 実際の出力ファイル名は、VectorTank 内部の実装に依存するが、
            # ここでは例として _vectors と _meta のファイルが作成されることをチェックする。
            vector_file = f"{expected_path}_{tank.tank_name}_vectors.npz"
            meta_file = f"{expected_path}_{tank.tank_name}_meta.pkl"
            self.assertTrue(os.path.exists(vector_file), "ベクトルファイルが作成されていません。")
            self.assertTrue(os.path.exists(meta_file), "メタデータファイルが作成されていません。")

    def test_default_store_dir(self):
        """
        store_dir が指定されなかった場合、カレントディレクトリが利用されることを検証します。
        """
        # カレントディレクトリの取得
        current_dir = os.getcwd()
        store = VectorStore()  # store_dir 未指定 → カレントディレクトリ利用
        tank = store.create_tank("default_dir_tank", 3, VectorSimMethod.COSINE, np.float32, persist=True)
        expected_path = os.path.join(current_dir, "default_dir_tank")
        self.assertEqual(tank.persistence_path, expected_path, "store_dir が未指定の場合、カレントディレクトリが利用される必要があります。")

if __name__ == '__main__':
    unittest.main()
