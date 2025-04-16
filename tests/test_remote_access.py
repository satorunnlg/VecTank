import unittest
import tempfile
import os
import time
from multiprocessing import Process
from vectank.server import TankServer
from vectank.client import TankClient
from vectank.core import VectorSimMethod
import numpy as np

def run_server_for_test(port, authkey, store_dir):
    # サーバ起動時に、あらかじめ "remote_test" タンクを作成
    server = TankServer(port=port, authkey=authkey, store_dir=store_dir)
    server.store.create_tank("remote_test", 3, VectorSimMethod.COSINE, np.float32)
    server.run()

class TestRemoteAccess(unittest.TestCase):
    def test_remote_store_access(self):
        """
        別プロセスで起動したサーバに対して、TankClient を用いてリモートアクセスが可能かを検証します。
        また、リモートタンクの filter_by_metadata による結果も確認します。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            port = 50100
            authkey = b'remotekey'
            # サーバを別プロセスで起動
            server_proc = Process(target=run_server_for_test, args=(port, authkey, tmpdir))
            server_proc.start()
            # サーバ起動を待機
            time.sleep(2)
            # クライアントからリモートストアに接続
            client = TankClient(address=('localhost', port), authkey=authkey)
            tank = client.get_tank("remote_test")
            self.assertIsNotNone(tank, "リモートの 'remote_test' タンクが取得できません。")
            
            # リモートタンクに複数ベクトルを追加 (各ベクトルに異なるメタデータ)
            vectors = np.array([[1,0,0], [0,1,0], [0,0,1]], dtype=np.float32)
            metadata_list = [
                {"label": "X", "score": 5},
                {"label": "Y", "score": 15},
                {"label": "X", "score": 25}
            ]
            keys = []
            for vec, meta in zip(vectors, metadata_list):
                key = tank.add_vector(vec, meta)
                keys.append(key)
            
            # filter_by_metadata を利用し、label "X" の項目のみを確認
            filtered_keys = tank.filter_by_metadata({"label": "X"})
            self.assertEqual(len(filtered_keys), 2, "リモートタンクの filter_by_metadata による抽出件数が正しくありません。")
            # search で部分的に一致する項目を検索
            results = tank.search(np.array([1,0,0], dtype=np.float32), top_k=1)
            self.assertGreaterEqual(len(results), 1, "リモートタンクの search 結果が得られません。")
            
            server_proc.terminate()
            server_proc.join()

if __name__ == '__main__':
    unittest.main()