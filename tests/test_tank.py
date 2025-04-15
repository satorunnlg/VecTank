# tests/test_tank.py

import unittest
import numpy as np
from vectank.tank import VectorTank
from vectank.core import VectorSimMethod

class TestVectorTank(unittest.TestCase):
    def setUp(self):
        """
        各テストケース実行前に、VectorTank インスタンスを初期化します。
        タンク名は "test"、ベクトルの次元数は 5、類似度計算方式は COSINE、データ型は np.float32 を使用。
        """
        self.tank = VectorTank("test", 5, VectorSimMethod.COSINE, np.float32)

    def test_add_and_search_vector(self):
        """
        単一のベクトル追加と検索を検証するテストです。
        ・5次元のベクトルをタンクに追加し、返されたキーが文字列であることを確認。
        ・同じベクトルを検索し、返される検索結果の件数とキーが正しいことを検証します。
        """
        vector = np.array([1, 2, 3, 4, 5], dtype=np.float32)
        key = self.tank.add_vector(vector, {"test": "data"})
        self.assertIsInstance(key, str, "追加されたベクトルのキーは文字列である必要があります。")
        
        # 同一のベクトルをクエリとして検索
        results = self.tank.search(vector, top_k=1)
        self.assertEqual(len(results), 1, "検索結果は1件であるべきです。")
        result_key, score, metadata = results[0]
        self.assertEqual(result_key, key, "検索結果のキーは追加されたベクトルのキーと一致しなければなりません。")

    def test_add_vectors_bulk(self):
        """
        複数ベクトルの一括追加機能を検証します。
        ・複数のベクトルとそのメタデータを一括で追加し、
          返されるキーの件数が入力したベクトル数と一致することを確認します。
        """
        num_vectors = 10
        dim = 5
        vectors = np.random.rand(num_vectors, dim).astype(np.float32)
        metadata_list = [{"id": i} for i in range(num_vectors)]
        keys = self.tank.add_vectors(vectors, metadata_list)
        self.assertEqual(len(keys), num_vectors, "返されたキーの件数は登録したベクトル数と一致する必要があります。")

    def test_update_vector(self):
        """
        ベクトルの更新機能を検証するテストです。
        ・まず 5 次元のベクトルをタンクに追加し、その後更新したベクトルとメタデータで更新を実施。
        ・更新後の検索結果が、更新されたベクトルおよびメタデータを反映していることを確認します。
        """
        original = np.array([1, 2, 3, 4, 5], dtype=np.float32)
        key = self.tank.add_vector(original, {"info": "original"})
        
        # 更新用の新しいベクトルとメタデータ
        new_vector = np.array([5, 4, 3, 2, 1], dtype=np.float32)
        self.tank.update_vector(key, new_vector, {"info": "updated"})
        
        # 更新後、クエリとして new_vector を指定して検索
        results = self.tank.search(new_vector, top_k=1)
        self.assertGreater(len(results), 0, "更新後の検索結果は1件以上である必要があります。")
        found_key, score, metadata = results[0]
        self.assertEqual(found_key, key, "更新されたベクトルのキーが一致する必要があります。")
        self.assertEqual(metadata.get("info"), "updated", "更新されたメタデータが反映されている必要があります。")

    def test_delete_vector(self):
        """
        ベクトル削除機能のテストです。
        ・ベクトルをタンクに追加した後、削除処理を実施し、
          そのベクトルが検索結果に含まれなくなっていることを確認します。
        """
        vector = np.array([1, 1, 1, 1, 1], dtype=np.float32)
        key = self.tank.add_vector(vector, {"delete": True})
        # ベクトルを削除する
        self.tank.delete(key)
        
        # 削除後の検索結果に対象のキーが含まれていないことを確認
        results = self.tank.search(vector, top_k=10)
        keys_in_results = [res[0] for res in results]
        self.assertNotIn(key, keys_in_results, "削除されたベクトルのキーは検索結果に含まれてはいけません。")

    def test_clear_tank(self):
        """
        タンクのクリア機能を検証するテストです。
        ・複数のベクトルを追加した後、clear() を呼び出しタンクを初期状態に戻すことができるか確認します。
        ・内部で保持するベクトル配列、メタデータ、キーとインデックスの対応情報が全てクリアされることを検証します。
        """
        # 5つのベクトルを一括追加
        vectors = np.random.rand(5, 5).astype(np.float32)
        metadata_list = [{"i": i} for i in range(5)]
        self.tank.add_vectors(vectors, metadata_list)
        # clear() を実行してタンクを初期化
        self.tank.clear()
        
        # 内部状態の再確認
        self.assertEqual(self.tank._vectors.size, 0, "タンク内のベクトル配列は空でなければなりません。")
        self.assertEqual(len(self.tank._metadata), 0, "タンク内のメタデータはクリアされている必要があります。")
        self.assertEqual(len(self.tank._key_to_index), 0, "キーとインデックスの対応情報はクリアされている必要があります。")

    def test_delete_vector_exception(self):
        """
        存在しないキーで delete() を呼び出した場合、KeyError が送出されることを検証します。
        """
        with self.assertRaises(KeyError):
            self.tank.delete("nonexistent_key")

    def test_update_vector_exception(self):
        """
        存在しないキーで update_vector() を呼び出した場合、KeyError が送出されることを検証します。
        """
        new_vector = np.array([5, 4, 3, 2, 1], dtype=np.float32)
        with self.assertRaises(KeyError):
            self.tank.update_vector("nonexistent_key", new_vector, {"info": "updated"})

    def test_delete_keys_bulk(self):
        """
        delete_keys() の一括削除機能を検証します。
        ・複数のベクトルを追加した後、delete_keys() を利用して一括削除を行い、
          削除されたキーのリストが正しく返され、タンクから削除されていることを確認します。
        """
        # 複数ベクトルの一括追加
        num_vectors = 5
        dim = 5
        vectors = np.random.rand(num_vectors, dim).astype(np.float32)
        metadata_list = [{"id": i} for i in range(num_vectors)]
        keys = self.tank.add_vectors(vectors, metadata_list)
        
        # 一部のキーを一括削除
        keys_to_delete = keys[1:4]
        deleted_keys = self.tank.delete_keys(keys_to_delete)
        self.assertEqual(set(deleted_keys), set(keys_to_delete), "削除されたキーは指定した一覧と一致する必要があります。")
        
        # 残存するキーが検索結果に含まれていないことを確認
        for key in keys_to_delete:
            # 検索結果全体から削除されたキーが見つからないことを検証
            results = self.tank.search(np.ones(dim, dtype=np.float32), top_k=10)
            result_keys = [res[0] for res in results]
            self.assertNotIn(key, result_keys, f"削除されたキー {key} は検索結果に含まれてはいけません。")

    def test_delete_keys_empty(self):
        """
        存在しないキーを渡した場合、delete_keys() が空のリストを返すことを検証します。
        """
        deleted_keys = self.tank.delete_keys(["nonexistent1", "nonexistent2"])
        self.assertEqual(deleted_keys, [], "存在しないキーの場合、空のリストが返される必要があります。")

if __name__ == '__main__':
    unittest.main()
