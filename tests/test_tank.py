import os
import threading
import pytest
from tempfile import TemporaryDirectory

# ここではvectankモジュールから主要クラスをインポートしている前提です
from vectank import Tank, TankStore, TankServer, TankClient


def test_add_search_update_delete():
    tank = Tank()
    # add_vector: ベクトルとメタデータを登録する
    vec = [0.1, 0.2, 0.3]
    metadata = {"label": "test"}
    vector_id = tank.add_vector(vec, metadata)  # メタデータは辞書として渡す
    
    # search: 登録したベクトルが正しく検索されることを確認
    results = tank.search(query=vec)
    assert any(item["id"] == vector_id for item in results)
    
    # update_vector: 新しいベクトルとメタデータで更新する
    new_vec = [0.9, 0.9, 0.9]  # 更新用の新しいベクトル
    update_metadata = {"label": "updated"}
    tank.update_vector(vector_id, new_vec, update_metadata)
    
    # update後は新しいベクトルで検索する
    results = tank.search(query=new_vec)
    for item in results:
        if item["id"] == vector_id:
            assert item["metadata"]["label"] == "updated"
    
    # delete_vector: 削除後に検索結果から消えることを確認
    tank.delete_vector(vector_id)
    results_after = tank.search(query=new_vec)
    assert not any(item["id"] == vector_id for item in results_after)


def test_add_vectors():
    tank = Tank()
    vectors = [
        [0.1, 0.2],
        [0.3, 0.4],
        [0.5, 0.6]
    ]
    metadata_list = [
        {"label": "vec1"},
        {"label": "vec2"},
        {"label": "vec3"}
    ]
    # add_vectors: 複数ベクトルの一括登録テスト
    ids = tank.add_vectors(vectors, metadata_list)
    for vector_id, vec in zip(ids, vectors):
        results = tank.search(query=vec)
        assert any(item["id"] == vector_id for item in results)


def test_persistence(tmp_path):
    # 永続化テスト用に一時ディレクトリを利用
    store_dir = tmp_path / "tank_store"
    store_dir.mkdir()
    tank_store = TankStore(store_dir=str(store_dir))
    
    # TankStore経由でタンクを作成し、永続化する
    tank = tank_store.create_tank("test_tank")
    vec = [1, 2, 3]
    vector_id = tank.add_vector(vec, label="persistent")
    tank.save()
    
    # 保存したファイルからタンクを再ロードし、データが復元されているかを検証
    new_tank = tank_store.load_tank("test_tank")
    results = new_tank.search(query=vec)
    assert any(item["id"] == vector_id for item in results)


def test_remote_access(tmp_path):
    # Remote accessのテスト: 一時ディレクトリを利用してTankStoreを初期化
    store_dir = tmp_path / "remote_tank_store"
    store_dir.mkdir()
    port = 8001  # テスト用のポート番号
    tank_store = TankStore(store_dir=str(store_dir))
    
    # TankServerをバックグラウンドスレッドで起動
    server = TankServer(store=tank_store, port=port)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    # TankClientを用いてサーバへアクセス、ベクトルの登録と検索を実施
    client = TankClient(host="localhost", port=port)
    vec = [0.7, 0.8, 0.9]
    vector_id = client.add_vector(vec, note="remote_test")
    results = client.search(query=vec)
    assert any(item["id"] == vector_id for item in results)
    
    # サーバのクリーンアップ
    server.shutdown()
    server_thread.join(timeout=1)