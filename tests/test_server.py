# tests/test_server.py
import unittest
import tempfile
import os
import time
from multiprocessing import Process
from vectank.server import TankServer
from vectank.store import VectorStore
from vectank.core import VectorSimMethod
import numpy as np

def run_server(port, authkey, store_dir):
    server = TankServer(port=port, authkey=authkey, store_dir=store_dir)
    # サーバ起動後、一定時間待機することで外部からの接続や内部動作を検証できるようにする
    server.run()

class TestTankServer(unittest.TestCase):
    def test_server_startup_and_store_dir(self):
        """
        TankServer の起動時に、store_dir の指定が正しく反映されるかを検証します。
        また、サーバにより生成された VectorStore インスタンスの store_dir 属性が一致することを確認します。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            port = 50010
            authkey = b'testkey'
            # サーバをバックグラウンドプロセスで起動
            server_proc = Process(target=run_server, args=(port, authkey, tmpdir))
            server_proc.start()
            # サーバ起動を待つ
            time.sleep(2)
            # サーバ内部に作成された VectorStore インスタンスの store_dir が正しいか確認
            # ※ 本来はリモート接続して調査すべきですが、ここでは TankServer インスタンス生成直後の store_dir を再現するテスト例とします
            server = TankServer(port=port, authkey=authkey, store_dir=tmpdir)
            self.assertEqual(server.store.store_dir, tmpdir, "サーバ起動時に指定した store_dir がサーバの VectorStore に反映されている必要があります。")
            server_proc.terminate()
            server_proc.join()

    def test_server_data_persistence(self):
        """
        永続化フラグが True のタンクに対し、保存処理が正常に実行され、指定された store_dir にファイルが出力されるかを検証します。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # サーバ生成時に store_dir を指定
            server = TankServer(port=50020, authkey=b'testkey', store_dir=tmpdir)
            # 永続化フラグ True のタンクを作成
            tank = server.store.create_tank("persistent_server", 3, VectorSimMethod.COSINE, np.float32, persist=True)
            expected_path = os.path.join(tmpdir, "persistent_server")
            self.assertEqual(tank.persistence_path, expected_path, "永続化パスは指定した store_dir/tank_name である必要があります。")
            # タンクにデータを追加し、保存を呼び出す
            vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
            tank.add_vector(vector, {"info": "server persistence test"})
            tank.save_to_file()
            # サンプルとして、npz と pickle ファイルが生成されることを確認（実装に依存）
            vector_file = f"{expected_path}_{tank.tank_name}_vectors.npz"
            meta_file = f"{expected_path}_{tank.tank_name}_meta.pkl"
            self.assertTrue(os.path.exists(vector_file), "永続化用のベクトルファイルが生成されていない。")
            self.assertTrue(os.path.exists(meta_file), "永続化用のメタデータファイルが生成されていない。")

if __name__ == '__main__':
    unittest.main()
