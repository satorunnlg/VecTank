"""
【概要】
  本ファイルには、共有メモリを利用してベクトルとメタデータの管理を行う VecTank クラスが定義されています。
  ・固定サイズの NumPy 配列を共有メモリ上に確保し、各操作（追加、複数追加、検索、更新、削除、フィルタ、クリア）を実装。
  ・persist=True の場合、指定ディレクトリ内に「タンク名.npz」「タンク名.pkl」として永続化ファイルを生成し、状態を保持／復元します。

【主なメソッド】
  - add_vector: 単一のベクトルとメタデータを追加
  - add_vectors: 複数のベクトルと対応するメタデータを一括追加
  - search: 指定した類似度計算方式によりクエリに近いベクトルを検索（SIM_METHODS を参照）
  - update_vector: 指定キーのベクトルとメタデータを更新
  - filter_by_metadata: 指定条件に合致するメタデータを持つベクトルのキー一覧を返す
  - delete, delete_keys: 単一または複数のベクトル削除後、内部データを再構築
  - clear: 全データをクリア
  - __str__: タンクの基本情報を文字列で返す（デバッグ用）
  
【注意点】
  - 全操作はロックによる排他制御下で行われ、複数のスレッド／プロセス間の同時アクセスに対応しています。
  - ベクトルのキーは「1-indexed」の文字列で自動採番されます。
"""

import os
import pickle
import numpy as np
from multiprocessing import shared_memory, Lock
from vectank.core import SIM_METHODS  # 類似度計算関数群
import time
import copy
import json

class VecTank:
    _lock = Lock()
    
    def __init__(self, tank_name: str, dim: int = 1200, max_capacity: int = 100000, single_meta_size: int = 4096,
                 persist: bool = False, sim_method: str = "COSINE"):
        """
        コンストラクタ
          tank_name: タンクの名称
          dim: 各ベクトルの次元数
          max_capacity: タンクに格納可能な最大ベクトル数
          persist: 永続化モード（ただし、ファイル操作は TankStore に依存）
          store_dir: 永続化に用いるディレクトリ（ファイル操作は外部で実施）
        """
        self.tank_name = tank_name
        self.dim = dim
        self.max_capacity = max_capacity
        self.persist = persist
        self.sim_method = sim_method
        self.dtype = np.dtype("float32")
        # 各ベクトルに対応するメタデータを保持する辞書
        self.metadata = {}
        # 共有メモリでメタデータ同期用の固定サイズバッファ確保（サイズは必要に応じて調整）
        self._meta_shm_single_size = single_meta_size
        # 永続化時に保存する補助情報（主に初期パラメータ）
        self.metadata["params"] = {
            "dim": self.dim,
            "dtype": self.dtype.name,
            "default_sim_method": self.sim_method,
            "max_capacity": self.max_capacity,
            "persist": self.persist,
            "tank_name": self.tank_name,
            "meta_shm_single_size": self._meta_shm_single_size
            }

    def create_shared_memory(self):
        """
        TankStore 側でのタンク生成時に呼び出されるメソッド。
        共有メモリを生成し、ベクトルデータとメタデータを格納するための NumPy 配列を作成します。
        共有メモリのサイズは、最大ベクトル数と次元数に基づいて計算されます。
        共有メモリの名前は、TankStore 側で指定されたものを使用します。
        """
        # 共有メモリ上に確保するバイト数を計算（float32 固定）
        size = self.max_capacity * self.dim * self.dtype.itemsize
        # 共有メモリブロックの生成（create=True）
        self.shm = shared_memory.SharedMemory(name=f"{self.tank_name}_vector", create=True, size=size)
        # 共有メモリ上の NumPy 配列としてベクトルデータを管理
        self.vectors = np.ndarray((self.max_capacity, self.dim), dtype=self.dtype, buffer=self.shm.buf)
        self.vectors.fill(0)
        # メタデータ用の共有メモリサイズを計算
        self._meta_shm_size = self._meta_shm_single_size * self.max_capacity
        # メタデータ用の共有メモリブロックを生成（create=True）
        self.meta_shm = shared_memory.SharedMemory(name=f"{self.tank_name}_meta", create=True, size=self._meta_shm_size)
        # 初期状態（空の辞書）を pickle 化して書き込み
        self._update_shared_metadata()
    
    def _update_shared_metadata(self):
        """
        self.metadata の内容を pickle 化して、共有メモリ meta_shm に書き込みます。
        """
        meta_bytes = pickle.dumps(self.metadata)
        if len(meta_bytes) > self._meta_shm_size:
            raise MemoryError("Serialized metadata exceeds shared memory size.")
        # 共有メモリバッファをクリアし、シリアライズしたデータを書き込み
        self.meta_shm.buf[:self._meta_shm_size] = b'\x00' * self._meta_shm_size
        self.meta_shm.buf[:len(meta_bytes)] = meta_bytes

    def attach_shared_memory(self):
        """
        VecTank 側でTankStore側のタンクを取得する際に呼び出されるメソッド。
        """
        # 共有メモリブロックの生成（create=True）
        self.shm = shared_memory.SharedMemory(name=f"{self.tank_name}_vector", create=False)
        # 共有メモリ上の NumPy 配列としてベクトルデータを管理
        self.vectors = np.ndarray((self.max_capacity, self.dim), dtype=self.dtype, buffer=self.shm.buf)
        # メタデータ用の共有メモリブロックを生成（create=True）
        self.meta_shm = shared_memory.SharedMemory(name=f"{self.tank_name}_meta", create=False)
        self.metadata = self._read_shared_metadata()
        self._parse_params(self.metadata.get("params"))

    def _read_shared_metadata(self):
        """
        共有メモリ meta_shm から pickle 化された辞書を読み出して
        元の self.metadata に戻し、返します。
        """
        # 1) バッファ全体をバイト列として取得
        raw = self.meta_shm.buf
        # 2) trailing '\x00' を除去（write時に余白をゼロクリアしているため）
        pickled = bytes(raw).rstrip(b'\x00')
        # 3) pickle をアンロードして辞書に戻す
        metadata = pickle.loads(pickled)
        # 必要なら self.metadata を更新してもよい
        self.metadata = metadata
        return metadata
    
    def _parse_params(self, params: dict):
        """
        共有メモリから読み込んだメタデータのパラメータをインスタンス変数に設定します。
        """
        if params is None:
            raise ValueError("metadata['params'] が存在しません")

        # 必要に応じて型をキャスト
        self.dim = int(params["dim"])
        # 文字列 'float32' → NumPy dtype に変換したいなら次のように
        self.dtype = np.dtype(params["dtype"])
        # そのまま文字列として保持するなら以下でも OK
        # self.dtype = params["dtype"]

        self.sim_method      = params["default_sim_method"]
        self.max_capacity    = int(params["max_capacity"])
        self.persist         = bool(params["persist"])
        self.tank_name       = params["tank_name"]
        self._meta_shm_single_size = int(params["meta_shm_single_size"])
        # メタデータ用の共有メモリサイズを計算
        self._meta_shm_size = self._meta_shm_single_size * self.max_capacity
        return

    @classmethod
    def send_command_to_store(cls, command: str, store_name: str = "tankstore_comm", timeout: float = 5.0) -> bool:
        """
        TankStore との通信用共有メモリ (store_name) に対してコマンドを送信します。
        コマンド送信後、共有メモリバッファ（uint8 配列）が全0になるまでポーリングし、
        完了（Ack）したかどうかを返します。
        """
        from multiprocessing import shared_memory
        import numpy as np, time

        try:
            comm_shm = shared_memory.SharedMemory(name=store_name, create=False)
        except FileNotFoundError:
            print(f"[ERROR] Communication SHM '{store_name}' not found.")
            return False

        with cls._lock:
            comm_buffer = np.ndarray((1024,), dtype=np.uint8, buffer=comm_shm.buf)
            # 送信前にバッファをクリア
            comm_buffer.fill(0)
            cmd_bytes = command.encode('utf-8') + b'\x00'
            comm_buffer[:len(cmd_bytes)] = np.frombuffer(cmd_bytes, dtype=np.uint8)
            print(f"[DEBUG] Command '{command}' sent to TankStore using shared mem '{store_name}'. Waiting for acknowledgment...")

            start_time = time.time()
            while time.time() - start_time < timeout:
                if not np.any(comm_buffer):
                    print("[DEBUG] Acknowledgment received from TankStore.")
                    comm_shm.close()
                    return True
                time.sleep(0.1)
            print("[ERROR] Acknowledgment not received within timeout.")
            comm_shm.close()
        return False

    @classmethod
    def create_tank(cls, tank_name: str, dim: int, persist: bool = False,
                    max_capacity: int = 10000, store_name: str = "tankstore_comm", single_meta_size: int = 4096, sim_method: str = "COSINE") -> "VecTank":
        """
        TankStore 側に通信して新規タンクを生成し、生成されたタンクインスタンスを返します。
        store_name を指定することで、複数サーバ環境での利用が可能となります。
        """

        create_cmd = f"create,{tank_name},{dim},{persist},{max_capacity},{single_meta_size},{sim_method}"
        if not cls.send_command_to_store(create_cmd, store_name=store_name):
            print("[ERROR] TankStore did not acknowledge tank creation.")
            return None

        print(f"[DEBUG] Tank '{tank_name}' created and restored via TankStore.")
        dummy = cls(tank_name, dim, max_capacity, single_meta_size, persist, sim_method)
        dummy.attach_shared_memory()
        dummy.store_name = store_name
        return dummy

    @classmethod
    def get_tank(cls, tank_name: str, store_name: str = "tankstore_comm") -> "VecTank":
        """
        TankStore 側に通信して、既存のタンクを取得して返します。
        store_name を指定することで、複数サーバ環境での利用が可能となります。
        """
        dummy = cls(tank_name)
        dummy.attach_shared_memory()
        dummy.store_name = store_name
        return dummy

    def add_vector(self, vector: np.ndarray, meta: dict):
        """
        単一のベクトルおよび紐づくメタデータを追加する。
          vector: 形状 (dim,) の NumPy 配列（float32 に変換されます）
          meta: ベクトルに関連付いたメタデータの辞書
        戻り値: 自動採番されたキー（1-indexed の文字列）
        """
        with self.__class__._lock:
            num_vectors = len(self)
            if num_vectors >= self.max_capacity:
                raise MemoryError("Tank capacity reached.")
            if vector.shape != (self.dim,):
                raise ValueError(f"Vector shape must be ({self.dim},).")
            vec = vector.astype(self.dtype, copy=False)
            self.vectors[num_vectors, :] = vec
            key = str(num_vectors + 1)
            self.metadata[key] = meta
            self._update_shared_metadata()
        return key

    def add_vectors(self, vectors: np.ndarray, metadata_list: list, keys: list = None) -> list:
        with self.__class__._lock:
            n = vectors.shape[0]
            if vectors.shape[1] != self.dim:
                raise ValueError(f"Each vector must have {self.dim} dimensions.")
            if len(metadata_list) != n:
                raise ValueError("Length of metadata_list must match number of vectors.")
            if keys is not None and len(keys) != n:
                raise ValueError("Length of keys must match number of vectors.")
            new_keys = []
            num_vectors = len(self)
            if num_vectors + n > self.max_capacity:
                raise MemoryError("Adding vectors exceeds capacity.")
            for i in range(n):
                key = str(num_vectors + i + 1) if keys is None else str(keys[i])
                vec = vectors[i].astype(self.dtype, copy=False)
                self.vectors[num_vectors + i, :] = vec
                self.metadata[key] = metadata_list[i]
                new_keys.append(key)
            self._update_shared_metadata()

        return new_keys

    def search(self, query: np.ndarray, top_k: int = 1, sim_method: str = None):
        with self.__class__._lock:
            if query.shape != (self.dim,):
                raise ValueError(f"Query vector must have shape ({self.dim},).")
            num_vectors = len(self)
            if num_vectors == 0:
                return []
            method = sim_method if sim_method is not None else self.sim_method
            method_key = method.lower()
            if method_key not in SIM_METHODS:
                raise ValueError(f"Unsupported similarity method: {method}")
            fun = SIM_METHODS[method_key]
            data = self.vectors[:num_vectors]
            scores = fun(data, query.astype(self.dtype))
            sorted_indices = np.argsort(-scores)[:top_k]
            results = []
            for i in sorted_indices:
                key = str(i + 1)
                results.append((key, float(scores[i]), self.vectors[i].copy(), self.metadata.get(key)))

        return results

    def update_vector(self, key: str, new_vector: np.ndarray, new_metadata: dict = None):
        with self.__class__._lock:
            idx = int(key) - 1
            num_vectors = len(self)
            if idx < 0 or idx >= num_vectors:
                raise KeyError(f"Key {key} does not exist.")
            if new_vector.shape != (self.dim,):
                raise ValueError(f"New vector must have shape ({self.dim},).")
            self.vectors[idx] = new_vector.astype(self.dtype)
            if new_metadata is not None:
                self.metadata[key] = new_metadata
            self._update_shared_metadata()


    def filter_by_metadata(self, conditions=None) -> list:
        with self.__class__._lock:
            if conditions is None:
                return []
            filtered = []
            for key, meta in self.metadata.items():
                if key == "params":
                    continue
                if callable(conditions):
                    if conditions(meta):
                        filtered.append(key)
                elif isinstance(conditions, dict):
                    if all(meta.get(k) == v for k, v in conditions.items()):
                        filtered.append(key)
                else:
                    raise TypeError("conditions must be a dict or callable.")

        return filtered

    def delete(self, key: str):
        with self.__class__._lock:
            # 1) キー→インデックス変換＆存在チェック
            idx = int(key) - 1
            count = len(self)
            if idx < 0 or idx >= count:
                raise KeyError(f"Key {key} does not exist.")

            # 2) vectors を前に詰める（in-place シフト）
            for i in range(idx, count - 1):
                self.vectors[i] = self.vectors[i + 1]
            # 空いた最後の行はゼロクリア
            self.vectors[count - 1].fill(0)

            # 3) metadata を再構築
            old_meta = self.metadata
            new_meta = {
                "params": copy.deepcopy(old_meta["params"]),
            }
            new_idx = 0
            # 数値キーのみ再割り当て
            for old_key, val in old_meta.items():
                if old_key in ("params", "count"):
                    continue
                if int(old_key) == idx + 1:
                    # 削除対象はスキップ
                    continue
                new_idx += 1
                new_meta[str(new_idx)] = val

            # 4) metadata を書き戻し
            self.metadata = new_meta
            self._update_shared_metadata()


    def delete_keys(self, keys: list) -> list:
        # 1) キー→0-indexed インデックスのセット
        try:
            del_idxs = {int(k) - 1 for k in keys}
        except ValueError:
            raise KeyError("キーはすべて 1-indexed の数値文字列である必要があります．")

        with self.__class__._lock:
            count = len(self)
            # 範囲チェック
            if any(idx < 0 or idx >= count for idx in del_idxs):
                raise KeyError(f"存在しないキーがあります: {keys}")

            # 2) 残すインデックスリストを作成
            keep_idxs = [i for i in range(count) if i not in del_idxs]
            new_count = len(keep_idxs)

            # 3) vectors を in-place で前詰め
            for new_i, old_i in enumerate(keep_idxs):
                self.vectors[new_i] = self.vectors[old_i]
            # 空いた後半部分はゼロクリア
            for i in range(new_count, count):
                self.vectors[i].fill(0)

            # 4) metadata を再構築
            old_meta = self.metadata
            new_meta = {
                "params": copy.deepcopy(old_meta["params"]),
            }
            for new_i, old_i in enumerate(keep_idxs):
                new_meta[str(new_i + 1)] = old_meta[str(old_i + 1)]

            # 5) 書き戻し
            self.metadata = new_meta
            self._update_shared_metadata()
        return keys

    def clear(self):
        with self.__class__._lock:
            self.vectors.fill(0)
            params = copy.deepcopy(self.metadata.get("params", {}))
            self.metadata.clear()
            self.metadata["params"] = params
            self._update_shared_metadata()

    def save(self):
        """
        ベクトルデータとメタデータをファイルに保存します。
        永続化モードが有効な場合にのみ動作し、store_dir 内に
          ・ {tank_name}.npz  … 有効なベクトルデータ（_num_vectors 件分）
          ・ {tank_name}.pkl  … メタデータ
        として保存します。
        """
        save_cmd = f"save,{self.tank_name}"
        if not VecTank.send_command_to_store(save_cmd, store_name=self.store_name):
            print("[ERROR] TankStore did not acknowledge tank save.")
            return
        pass
    
    def out_log(self, message: str = None):
        """
        タンクの状態をログに出力します。
        """
        log_cmd = f"log,{self.tank_name},{message if message else ''}"
        if not VecTank.send_command_to_store(log_cmd, store_name=self.store_name):
            print("[ERROR] TankStore did not acknowledge tank log.")
            return
        pass

    def close(self):
        try:
            self.shm.close()
            self.meta_shm.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __len__(self):
        return len(self.metadata.keys()) - 1  # "params" を除外

    def __str__(self):
        # return f"VecTank({json.dumps(self.metadata.get("params", {}), indent=2)},\nlen={len(self)})"
        return f"VecTank({self.tank_name}, dim={self.dim}, max_capacity={self.max_capacity}, len={len(self)}, persist={self.persist}, sim_method={self.sim_method})"


# ----------------------------------------------------------------------
# 動作確認用サンプルコード（単体テスト）
# ----------------------------------------------------------------------
if __name__ == '__main__':
    import os
    import numpy as np
    import time

    print("=== VecTank 動作確認 ===")

    # create_tank を用いて "test_tank" を生成
    tank = VecTank.create_tank("test_tank", dim=3, persist=True)
    if tank is None:
        print("[ERROR] TankStore によるタンク生成に失敗しました。")
        os._exit(1)
    else:
        print("Created Tank:", tank)

    # 単一ベクトル追加
    vec = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    key1 = tank.add_vector(vec, {"info": "first vector"})
    print(f"[DEBUG] Added vector key: {key1}")
    tank.out_log("Added first vector")

    # 複数ベクトル一括追加
    vectors = np.array([[4.0, 5.0, 6.0],
                        [7.0, 8.0, 9.0]], dtype=np.float32)
    keys = tank.add_vectors(vectors, [{"info": "second vector"}, {"info": "third vector"}])
    print(f"[DEBUG] Added vector keys: {keys}")
    tank.out_log("Added second and third vectors")

    # 類似度検索（デフォルトは COSINE）
    query = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    results = tank.search(query, top_k=2)
    print(f"[DEBUG] Search results: {results}")

    # update_vector のテスト：1番目のベクトルを更新
    tank.update_vector(key1, np.array([9.0, 8.0, 7.0], dtype=np.float32), {"info": "updated first vector"})
    results_after_update = tank.search(np.array([9.0, 8.0, 7.0], dtype=np.float32), top_k=1)
    print(f"[DEBUG] Search after update: {results_after_update}")
    tank.out_log("Updated first vector")

    # filter_by_metadata テスト：メタデータに "updated" が含まれるものを抽出
    filtered_keys = tank.filter_by_metadata(lambda meta: "updated" in meta.get("info", ""))
    print(f"[DEBUG] Filtered keys: {filtered_keys}")

    # delete_keys テスト：追加したすべてのベクトルを削除
    all_keys = [key1] + keys
    deleted_keys = tank.delete_keys(all_keys)
    print(f"[DEBUG] Deleted keys: {deleted_keys}")
    print(f"[DEBUG] Vector count after deletion: {len(tank)}")
    tank.out_log("Deleted all vectors")

    # 再度ベクトル追加して clear の動作確認
    tank.add_vector(np.array([10.0, 20.0, 30.0], dtype=np.float32), {"info": "new vector"})
    tank.out_log("Added new vector")
    print(f"[DEBUG] Vector count before clear: {len(tank)}")
    tank.clear()
    print(f"[DEBUG] Vector count after clear: {len(tank)}")
    tank.out_log("Cleared all vectors")

    # 永続化のテスト（save() は空実装）
    tank.add_vector(np.array([5.0, 5.0, 5.0], dtype=np.float32), {"info": "persisted vector"})
    tank.out_log("Added vector for persistence test")
    tank.save()
    print("[DEBUG] Tank saved successfully.")
    print("[DEBUG] Tank :", str(tank))
    print("=== VecTank 動作確認完了 ===")
    tank.close()
