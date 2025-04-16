import unittest
import time
import numpy as np
from multiprocessing import Process, Queue
from vectank.client import TankClient
from vectank.core import VectorSimMethod

# プロセス A：タンクにベクトルを追加し、結果をプロセス B に送信する
def client_A(queue_A_to_B, queue_B_to_A, port, authkey):
    client = TankClient(address=('localhost', port), authkey=authkey)
    # "shared_tank" がなければ作成
    try:
        tank = client.create_tank("shared_tank", 3, VectorSimMethod.COSINE, np.float32)
    except Exception:
        tank = client.get_tank("shared_tank")
    # プロセス A がベクトルを追加（source=A）
    vector_A = np.array([1, 2, 3], dtype=np.float32)
    key_A = tank.add_vector(vector_A, {"source": "A"})
    # プロセス A は key_A をプロセス B に送信する
    queue_A_to_B.put(key_A)
    # プロセス A はプロセス B が追加したベクトルを取得するため待機
    try:
        key_B = queue_B_to_A.get(timeout=10)
    except Exception as e:
        raise Exception("Process A timed out waiting for B's vector.") from e
    # 検索: プロセス A は、プロセス B が追加したと期待するベクトル ([4,5,6]) を検索
    results = tank.search(np.array([4, 5, 6], dtype=np.float32), top_k=1)
    if results:
        found_key, score, result_vector, meta = results[0]
        if meta.get("source") != "B":
            raise Exception("Process A: Retrieved vector metadata does not indicate source B.")
    else:
        raise Exception("Process A: No results found for B's vector.")

# プロセス B：プロセス A から追加されたベクトルを取得し、自身もベクトルを追加する
def client_B(queue_A_to_B, queue_B_to_A, port, authkey):
    client = TankClient(address=('localhost', port), authkey=authkey)
    # "shared_tank" を取得（なければ作成）
    try:
        tank = client.create_tank("shared_tank", 3, VectorSimMethod.COSINE, np.float32)
    except Exception:
        tank = client.get_tank("shared_tank")
    # プロセス B は、プロセス A から送られてきた key を受信し、A のベクトルを検証する
    try:
        key_A = queue_A_to_B.get(timeout=10)
    except Exception as e:
        raise Exception("Process B timed out waiting for A's vector.") from e
    results = tank.search(np.array([1, 2, 3], dtype=np.float32), top_k=1)
    if results:
        found_key, score, result_vector, meta = results[0]
        if meta.get("source") != "A":
            raise Exception("Process B: Retrieved vector metadata does not indicate source A.")
    else:
        raise Exception("Process B: No results found for A's vector.")
    # プロセス B が新たにベクトルを追加（source=B）
    vector_B = np.array([4, 5, 6], dtype=np.float32)
    key_B = tank.add_vector(vector_B, {"source": "B"})
    # key_B をプロセス A に送信
    queue_B_to_A.put(key_B)

class TestTankRemoteAccess(unittest.TestCase):
    def test_two_processes_shared_access(self):
        """
        TankClient を別プロセス間で使用し、
        プロセス A で追加されたベクトルがプロセス B から取得でき、
        逆方向も同様に取得可能であることを検証します。
        """
        port = 50200
        authkey = b'remotekey'
        queue_A_to_B = Queue()
        queue_B_to_A = Queue()
        
        proc_A = Process(target=client_A, args=(queue_A_to_B, queue_B_to_A, port, authkey))
        proc_B = Process(target=client_B, args=(queue_A_to_B, queue_B_to_A, port, authkey))
        
        # 両プロセスを開始
        proc_A.start()
        proc_B.start()
        
        # 両プロセスの終了を待機
        proc_A.join(timeout=20)
        proc_B.join(timeout=20)
        
        self.assertFalse(proc_A.is_alive(), "Process A did not finish in time.")
        self.assertFalse(proc_B.is_alive(), "Process B did not finish in time.")

if __name__ == '__main__':
    unittest.main()