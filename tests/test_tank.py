# tests/test_tank.py

import unittest
import tempfile
import os
import numpy as np
from vectank.tank import VectorTank
from vectank.core import VectorSimMethod

class TestVectorTank(unittest.TestCase):
    
    def setUp(self):
        """
        各テストケース実行前に、VectorTank インスタンスを初期化します。
        永続化機能については、persist=False の状態で初期化します。
        """
        self.dim = 3
        self.tank = VectorTank("testtank", self.dim, VectorSimMethod.COSINE, np.float32, persist=False, file_path=None)
    
    def test_add_and_search_vector(self):
        """
        単一のベクトルを追加し、保存した結果を search() で検索できることを検証します。
        """
        vector = np.array([1, 2, 3], dtype=np.float32)
        metadata = {"desc": "test vector"}
        key = self.tank.add_vector(vector, metadata)
        self.assertIsInstance(key, str, "add_vector の戻り値は文字列である必要があります。")
        results = self.tank.search(vector, top_k=1)
        self.assertGreaterEqual(len(results), 1, "検索結果は1件以上返る必要があります。")
        found_key, score, result_vector, result_metadata = results[0]
        self.assertEqual(found_key, key, "検索結果のキーは追加時のキーと一致する必要があります。")
    
    def test_update_vector(self):
        """
        追加済みのベクトルに対し、更新処理が正しく動作するか検証します。
        """
        vector = np.array([1, 1, 1], dtype=np.float32)
        metadata = {"desc": "initial"}
        key = self.tank.add_vector(vector, metadata)
        new_vector = np.array([2, 2, 2], dtype=np.float32)
        new_metadata = {"desc": "updated"}
        self.tank.update_vector(key, new_vector, new_metadata)
        results = self.tank.search(new_vector, top_k=1)
        found_key, score, result_vector, result_metadata = results[0]
        self.assertEqual(found_key, key, "更新後の検索結果のキーが一致しません。")
        self.assertEqual(result_metadata, new_metadata, "更新後のメタデータが一致しません。")
    
    def test_delete_vector(self):
        """
        追加したベクトルを削除し、検索結果に反映されるか検証します。
        """
        vector = np.array([3, 3, 3], dtype=np.float32)
        metadata = {"delete": True}
        key = self.tank.add_vector(vector, metadata)
        self.tank.delete(key)
        results = self.tank.search(vector, top_k=1)
        if results:
            found_key, score, result_vector, result_metadata = results[0]
            self.assertNotEqual(found_key, key, "削除済みのキーが検索結果に現れてはなりません。")
        else:
            self.assertEqual(len(results), 0, "削除後は検索結果が返らないはずです。")
    
    def test_persistence_save_and_load(self):
        """
        永続化フラグ True のタンクについて、save_to_file() により永続化ファイルが作成され、
        load_from_file() で状態が復元されることを検証します。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # persist=True でタンクを作成し、store_dir の指定として tmpdir を使用
            persist_path = os.path.join(tmpdir, "persistent")
            tank = VectorTank("persistent", self.dim, VectorSimMethod.COSINE, np.float32, persist=True, file_path=persist_path)
            vector = np.array([4, 4, 4], dtype=np.float32)
            metadata = {"persist": True}
            key = tank.add_vector(vector, metadata)
            # 保存処理を実行
            tank.save_to_file()
            # 永続化用ファイル名は実装に依存しますが、ここでは例としてファイルの存在をチェック
            vector_file = f"{tank.persistence_path}_{tank.tank_name}_vectors.npz"
            meta_file = f"{tank.persistence_path}_{tank.tank_name}_meta.pkl"
            self.assertTrue(os.path.exists(vector_file), "永続化用のベクトルファイルが作成されていません。")
            self.assertTrue(os.path.exists(meta_file), "永続化用のメタデータファイルが作成されていません。")
            # 新しいタンクインスタンスを作成し、load_from_file() で状態を復元
            new_tank = VectorTank("persistent", self.dim, VectorSimMethod.COSINE, np.float32, persist=True, file_path=persist_path)
            new_tank.load_from_file()
            results = new_tank.search(vector, top_k=1)
            self.assertGreaterEqual(len(results), 1, "load_from_file 後、追加したベクトルが検索結果に現れる必要があります。")
            found_key, score, result_vector, result_metadata = results[0]
            self.assertEqual(found_key, key, "復元されたタンクの検索結果のキーが一致しません。")

class TestVectorTankMetadata(unittest.TestCase):
    def setUp(self):
        self.dim = 3
        # 永続化は不要として初期化
        self.tank = VectorTank("meta_test", self.dim, VectorSimMethod.COSINE, np.float32, persist=False, file_path=None)
    
    def test_search_and_filter_by_metadata(self):
        """
        複数のベクトルを追加し、search() および filter_by_metadata() の結果が
        追加時の各メタデータと正しく紐づいているかを検証します。
        """
        # 異なるメタデータを付与して複数ベクトルを追加
        vectors = np.array([[1,0,0], [0,1,0], [0,0,1]], dtype=np.float32)
        metadata_list = [
            {"group": "A", "value": 10},
            {"group": "B", "value": 20},
            {"group": "A", "value": 30}
        ]
        keys = []
        for vec, meta in zip(vectors, metadata_list):
            key = self.tank.add_vector(vec, meta)
            keys.append(key)
        
        # search() でクエリと一致する項目を取得
        # 例えば、[1,0,0] で検索して、最も類似度の高い項目が group "A" であることを確認
        results = self.tank.search(np.array([1,0,0], dtype=np.float32), top_k=1)
        self.assertGreaterEqual(len(results), 1, "search 結果は1件以上返る必要があります。")
        found_key, score, found_vector, found_metadata = results[0]
        self.assertEqual(found_metadata["group"], "A", "search で返されたメタデータが正しくない。")
        
        # filter_by_metadata() で、group が "A" の項目のみを抽出
        filtered_keys = self.tank.filter_by_metadata({"group": "A"})
        # 追加したうち、2件が group "A" であるはず
        self.assertEqual(len(filtered_keys), 2, "filter_by_metadata で抽出された件数が正しくありません。")
        # 各キーに対して、値の確認
        for key in filtered_keys:
            meta = self.tank._metadata.get(key)
            self.assertIsNotNone(meta, "フィルタ後のキーに対応するメタデータが見つかりません。")
            self.assertEqual(meta.get("group"), "A", "フィルタされたメタデータの group が期待値と異なります。")

if __name__ == '__main__':
    unittest.main()
