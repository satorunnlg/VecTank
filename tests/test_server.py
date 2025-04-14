# tests/test_server.py
import unittest
from vectank.server import VectorDBServer
from vectank.core import VectorSimMethod
import numpy as np
import time
import threading

class TestVectorDBServer(unittest.TestCase):
    def test_server_startup_and_shutdown(self):
        server = VectorDBServer(port=50051, authkey=b'secret', save_file=None)
        server.db.create_table("test", 10, VectorSimMethod.COSINE, np.float32)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(1)
        self.assertTrue(thread.is_alive())
        # サーバは daemon スレッドのため、テスト終了時に停止

if __name__ == '__main__':
    unittest.main()
