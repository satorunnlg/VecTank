import os
import time
import threading
import pytest
from tempfile import TemporaryDirectory

from vectank import TankServer, TankStore, TankClient

def run_server_in_thread(server):
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    # サーバ起動のため少し待機
    time.sleep(1)
    return server_thread

def test_server_startup_and_shutdown(tmp_path):
    store_dir = tmp_path / "tank_store"
    store_dir.mkdir()
    tank_store = TankStore(store_dir=str(store_dir))
    
    # 使用するポート番号（テスト用）
    port = 8002
    server = TankServer(store=tank_store, port=port)
    server_thread = run_server_in_thread(server)
    
    # TankClientによりサーバへの通信確認
    client = TankClient(host="localhost", port=port)
    tank_name = "server_test_tank"
    # クライアント経由でタンクの作成（TankClient.create_tankが存在する前提）
    client.create_tank(tank_name)
    
    vec = [7, 8, 9]
    # 修正: メタデータを辞書で渡す
    vector_id = client.add_vector(vec, {"note": "server_test"})
    results = client.search(query=vec)
    assert any(item["id"] == vector_id for item in results)
    
    # サーバのシャットダウン
    server.shutdown()
    server_thread.join(timeout=5)
    
    # サーバ停止後、クライアントでの操作が失敗することを検証
    with pytest.raises(Exception):
        client.search(query=vec)