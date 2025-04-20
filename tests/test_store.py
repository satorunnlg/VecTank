import os
import pytest
from tempfile import TemporaryDirectory

# vectankモジュールからTankStoreおよびTankをインポートする前提です。
from vectank import TankStore, Tank

def test_create_and_get_tank(tmp_path):
    store_dir = tmp_path / "tank_store"
    store_dir.mkdir()
    tank_store = TankStore(store_dir=str(store_dir))
    
    # タンクの作成
    tank = tank_store.create_tank("test_tank")
    assert isinstance(tank, Tank)
    
    # 取得したタンクでベクトルの追加と検索が可能なことを確認
    vec = [1, 2, 3]
    # 修正: メタデータを辞書で渡す
    vector_id = tank.add_vector(vec, {"label": "store_test"})
    fetched_tank = tank_store.get_tank("test_tank")
    results = fetched_tank.search(query=vec)
    assert any(item["id"] == vector_id for item in results)

def test_duplicate_tank_creation(tmp_path):
    store_dir = tmp_path / "tank_store"
    store_dir.mkdir()
    tank_store = TankStore(store_dir=str(store_dir))
    
    # 同一名タンクの2回生成で例外が発生することを確認
    _ = tank_store.create_tank("test_tank")
    with pytest.raises(Exception):
        tank_store.create_tank("test_tank")

def test_delete_tank(tmp_path):
    store_dir = tmp_path / "tank_store"
    store_dir.mkdir()
    tank_store = TankStore(store_dir=str(store_dir))
    
    # タンクの作成と削除
    _ = tank_store.create_tank("test_tank")
    tank_store.delete_tank("test_tank")
    
    # 削除後の取得で例外またはNoneが返されることを期待
    with pytest.raises(Exception):
        tank_store.get_tank("test_tank")

def test_persistence_files(tmp_path):
    store_dir = tmp_path / "tank_store"
    store_dir.mkdir()
    tank_store = TankStore(store_dir=str(store_dir))
    
    # 永続化対象のタンク作成とデータ登録
    tank = tank_store.create_tank("persist_tank")
    vec = [4, 5, 6]
    # 修正: メタデータを辞書で渡す
    vector_id = tank.add_vector(vec, {"label": "persistence"})
    
    # タンクの保存処理を実行
    tank.save()
    
    # 保存先ディレクトリに永続化ファイルが作成されているか検証
    # ※拡張子やファイル名は実装に合わせてください
    persistence_file = os.path.join(str(store_dir), "persist_tank.npz")
    assert os.path.exists(persistence_file)