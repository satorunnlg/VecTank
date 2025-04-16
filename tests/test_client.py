# tests/test_client.py
#
# このテストは、TankClient クラスの基本機能を検証します。
# 具体的には、以下の項目についてテストを行います:
# 1. defaultタンクの作成と取得 (create_tank/get_tank)
# 2. 単一ベクトルの追加 (add_vector)
# 3. 類似度検索機能 (search)
#
# TankClient はリモートストアに接続し、タンク操作（タンクの作成、取得、ベクトルの追加、検索）
# を行うためのクライアントAPIです。

import unittest
from vectank.client import TankClient  # 旧 VectorDBClient → TankClient に名称統一
from vectank.core import VectorSimMethod
import numpy as np

class TestTankClient(unittest.TestCase):
    def setUp(self):
        """
        各テストケースの実行前に、TankClient インスタンスを生成し、
        defaultタンク "default" を明示的に作成または取得します。
        """
        self.client = TankClient()
        # 既存の "default" タンクが存在するか確認し、なければ作成する
        existing = self.client.get_tank("default")
        if existing is None:
            self.tank = self.client.create_tank("default", 1200, VectorSimMethod.COSINE, np.float32)
        else:
            self.tank = existing

    def test_get_tank(self):
        """
        get_tank() メソッドで "default" タンクを取得できるか検証します。
        タンクが None でないことを確認します。
        """
        # setUpですでに "default" タンクを作成済みなので、改めて get_tank() で取得する
        tank = self.client.get_tank("default")
        self.assertIsNotNone(tank, "Default tank should not be None.")

    def test_add_vector(self):
        """
        add_vector() メソッドのテスト:
        1200 次元のベクトルを生成し、タンクに追加した際に
        戻り値としてキーが正しく返されることを確認します。
        """
        dim = 1200
        vector = np.ones(dim, dtype=np.float32)  # 全要素が1のベクトルを生成
        metadata = {"description": "test vector"}
        key = self.tank.add_vector(vector, metadata)
        self.assertIsInstance(key, str, "Returned key should be a string.")

    def test_search(self):
        """
        search() メソッドのテスト:
        既知のパターンを持つベクトルをタンクに追加し、そのベクトルと
        同じ内容のベクトルで検索した場合、最も類似度の高い結果として
        正しいキーが返されるか検証します。
        """
        dim = 1200
        # すべての要素が 0.5 のベクトルを生成
        vector = np.full(dim, 0.5, dtype=np.float32)
        metadata = {"pattern": "half"}
        key = self.tank.add_vector(vector, metadata)
        
        # 追加したベクトルをクエリとして検索
        results = self.tank.search(vector, top_k=1)
        self.assertGreater(len(results), 0, "Search should return at least one result.")
        
        # search の戻り値は (key, score, vector, metadata) となっているので、4要素でアンパック
        result_key, score, result_vector, result_metadata = results[0]
        self.assertEqual(result_key, key, "The most similar vector's key should match the added vector's key.")

if __name__ == '__main__':
    unittest.main()
