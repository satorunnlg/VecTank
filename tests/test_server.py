# tests/test_server.py
import unittest
from vectank.server import TankServer  # VectorDBServer → TankServer に名称統一
from vectank.core import VectorSimMethod
import numpy as np
import time
import threading

class TestTankServer(unittest.TestCase):
    def test_server_startup_and_shutdown(self):
        """
        TankServer を起動して稼働確認を行うテストです。
        ・TankServer のインスタンスを生成し、"test" タンクを作成。
        ・サーバーを daemon スレッドとして起動し、一定時間後にスレッドが生存していることを確認します。
        ※ サーバは daemon スレッドのため、テスト終了時に自動的に停止します。
        """
        server = TankServer(port=50051, authkey=b'secret', save_file=None)
        # タンク名 "test" で新たにタンクを作成。create_table → create_tank へ名称統一
        server.store.create_tank("test", 10, VectorSimMethod.COSINE, np.float32)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(1)
        self.assertTrue(thread.is_alive(), "サーバースレッドが起動しているはずです。")
    
    def test_server_data_persistence(self):
        """
        TankServer の停止時に、各タンクのデータ保存処理が正しく動作するかを検証するテストです。
        ・save_file を指定して TankServer インスタンスを生成し、タンクにデータを追加します。
        ・KeyboardInterrupt 発生時に各タンクの save_to_file() メソッドが例外なく実行されるかを、
          シミュレーション的に検証します。
        ※ 本テストでは実際のファイル出力は行わず、保存処理の例外発生の有無を確認します。
        """
        server = TankServer(port=50052, authkey=b'secret', save_file="temp_test")
        # "persistence_test" タンクを作成し、簡易的なデータを追加
        tank = server.store.create_tank("persistence_test", 5, VectorSimMethod.INNER, np.float32)
        vector = np.ones(5, dtype=np.float32)
        tank.add_vector(vector, {"info": "test persistence"})
        
        # サーバーの run() メソッド内では KeyboardInterrupt 発生時に保存処理が呼ばれる仕様なので、
        # 本テストでは直接 save_to_file() を呼び出して例外発生しないことを確認する
        try:
            for t in server.store.tanks.values():
                t.save_to_file()
        except Exception as e:
            self.fail(f"保存処理で例外が発生しました: {e}")
        
        # サーバーを daemon スレッドで起動し、稼働中であることを簡易確認
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(1)
        self.assertTrue(thread.is_alive(), "サーバースレッドが起動しているはずです。")
        thread.join(timeout=1)  # daemon のため、join 後に自動停止

if __name__ == '__main__':
    unittest.main()
