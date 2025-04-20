"""
【概要】
  本ファイルは、複数のタンク（VecTank インスタンス）を一元管理する TankStore クラスを定義しています。
  
  TankStore の主な役割：
    - 指定ディレクトリ(store_dir)内の永続化ファイル（.npz）をスキャンし、タンクを自動復元する。
    - 新規タンク作成(create_tank)や、既存タンクの取得(get_tank)のインターフェースを提供する。
    - 通信用共有メモリを用いた VecTank 側からのコマンド受付と、
      イベントループでのコマンド処理を行う。
  
【注意点】
  - 永続化ファイルは、タンク名に基づいて "{tank_name}.npz"（および対応する .pkl）として保存されます。
  - 自動復元時は、仮に次元128、最大容量10000として復元を試みますが、
    実際はメタデータから取得する等の改良が必要です。
"""

import os
import pickle
import time
import numpy as np
import threading
from multiprocessing import shared_memory, Lock, resource_tracker
from vectank.tank import VecTank
import traceback

class TankStore:
    """
    TankStore クラスは、複数の VecTank インスタンスを管理します。
    サーバ（またはその他のアプリケーション）が起動時に、store_dir 内の永続化ファイルを基に、
    既存タンクを自動復元するとともに、通信用共有メモリ経由で VecTank からの要求を処理します。
    """
    _lock = Lock()  # スレッドセーフな操作を保証するためのロック
    
    def __init__(self, store_dir: str = None, store_name: str = "tankstore_comm"):
        """
        コンストラクタ
          store_dir: 永続化ファイルの格納ディレクトリ。指定がなければカレントディレクトリを利用。
          store_name: 通信用共有メモリの名前。デフォルトは "tankstore_comm"。
        """
        self.store_dir = store_dir if store_dir is not None else os.getcwd()
        self.tanks = {}  # タンク名をキーとした VecTank インスタンスの辞書
        self._load_all_tanks()

        # 通信用共有メモリの生成
        # store_name を元に共有メモリ名を設定
        self._comm_shm_name = store_name
        self._comm_shm_size = 1024  # 固定サイズ（必要に応じて調整）
        try:
            # 既に存在している場合はアタッチ
            self._comm_shm = shared_memory.SharedMemory(name=self._comm_shm_name, create=False)
        except FileNotFoundError:
            # 存在しなければ新規作成
            self._comm_shm = shared_memory.SharedMemory(name=self._comm_shm_name, create=True, size=self._comm_shm_size)
        # 通信用バッファ（uint8 配列として扱う）
        self._comm_buffer = np.ndarray((self._comm_shm_size,), dtype=np.uint8, buffer=self._comm_shm.buf)
        # 初期化：全バイトを 0 にセット
        self._comm_buffer.fill(0)

        # イベントループの停止用フラグ
        self._stop_event = threading.Event()
        # イベントループスレッドの生成
        self._event_thread = threading.Thread(target=self.event_loop, daemon=True)
        self._event_thread.start()

    def create_tank(self, tank_name: str, dim: int, persist: bool = False, max_capacity: int = 10000, single_meta_size: int = 4096, sim_method: str = "COSINE"):
        """
        新規タンクを作成し管理辞書に登録する
          tank_name: タンク名（重複は不可）
          dim: タンク内の各ベクトルの次元数
          persist: 永続化モードを有効にする場合 True
          max_capacity: タンクが保持可能な最大ベクトル数
        戻り値:
          作成された VecTank インスタンス
        """
        if tank_name in self.tanks:
            raise ValueError(f"Tank '{tank_name}' already exists.")
        tank = VecTank(tank_name, dim, max_capacity, single_meta_size, persist, sim_method)
        print(f"[DEBUG] create tank: {tank.tank_name}")
        tank.create_shared_memory()
        print(f"[DEBUG] create shared memory: {tank.tank_name}")
        self.tanks[tank_name] = tank
        print(f"[DEBUG] regist tank to store: {tank.tank_name}")
        return tank

    def get_tank(self, tank_name: str):
        """
        指定されたタンク名の VecTank インスタンスを返す。
        存在しなければ None を返す。
        """
        return self.tanks.get(tank_name)

    def _load_all_tanks(self):
        """
        指定した store_dir 内の永続化ファイル（拡張子 .npz）を検出し、
        それらに対応するタンクを自動復元する。
        ここでは、ファイル名からタンク名を推定し、仮に次元を 128、最大容量を 10000 として
        VecTank インスタンスを生成します。さらに、対応する拡張子 .pkl のメタデータファイルがあれば読み込み、
        その内容を共有メモリに同期します。
        """
        import pickle  # _load_all_tanks 内で利用するためインポート
        with self.__class__._lock:
            for file in os.listdir(self.store_dir):
                if file.endswith(".npz"):
                    # ファイル名から拡張子を除いた部分をタンク名とする
                    tank_name = file[:-4]
                    if tank_name not in self.tanks:
                        try:
                            # タンクの復元処理
                            tank = VecTank(tank_name)
                            # pklファイルが存在する場合はメタデータを読み込む
                            meta_path = os.path.join(self.store_dir, f"{tank_name}.pkl")
                            if os.path.exists(meta_path):
                                with open(meta_path, "rb") as f:
                                    metadata = pickle.load(f)
                                print(f"[DEBUG] Loaded metadata for tank: {tank_name}")
                                # tank._read_shared_metadata()
                                tank._parse_params(metadata.get("params", {}))
                                tank.create_shared_memory()
                                meta_bytes = pickle.dumps(metadata)
                                if len(meta_bytes) > tank._meta_shm_size:
                                    raise MemoryError("Serialized metadata exceeds shared memory size.")
                                # 共有メモリバッファをクリアし、シリアライズしたデータを書き込み
                                tank.meta_shm.buf[:tank._meta_shm_size] = b'\x00' * tank._meta_shm_size
                                tank.meta_shm.buf[:len(meta_bytes)] = meta_bytes
                                tank._read_shared_metadata()

                            # ベクトルデータの読み込み
                            vector_path = os.path.join(self.store_dir, f"{tank_name}.npz")
                            if os.path.exists(vector_path):
                                # ベクトルデータを読み込み
                                with np.load(vector_path) as data:
                                    loaded_vectors = data["vectors"]
                                    tank.vectors[:loaded_vectors.shape[0]] = loaded_vectors
                                 
                            print(f"[DEBUG] Restored metadata for tank: {str(tank)}")
                            
                            self.tanks[tank_name] = tank
                            print(f"[DEBUG] Restored tank: {tank_name}")
                        except Exception as e:
                            print(f"[ERROR] Failed to restore tank '{tank_name}': {e}")
                            traceback.print_exc()

    def event_loop(self):
        """
        共有メモリ経由で VecTank 側からのコマンドを受信し、イベントループで処理を行う。
        対応コマンド:
          - create,<tank_name>,<dim>,<persist>,<max_capacity>,<store_dir>
          - save,<tank_name>
        なお、コマンド処理後は共有メモリバッファを全0にクリアして完了通知とする。
        """
        print("[DEBUG] TankStore event loop started.")
        self._loop = True
        while not self._stop_event.is_set():
            if self._comm_buffer[0] != 0:
                # 共有メモリからコマンド文字列を取得（null-terminated とする）
                raw_bytes = bytes(self._comm_buffer)
                cmd = raw_bytes.split(b'\x00')[0].decode('utf-8')
                print(f"[DEBUG] Received command: {cmd}")

                parts = cmd.split(',')
                command_name = parts[0].lower()
                if command_name == "create":
                    # コマンド例: "create,sample_tank,3,True,10000,/path/to/dir"
                    try:
                        if len(parts) >= 6:
                            tank_name = parts[1]
                            dim = int(parts[2])
                            persist = True if parts[3].lower() == "true" else False
                            max_capacity = int(parts[4])
                            single_meta_size = int(parts[5])
                            sim_method = parts[6]
                            if tank_name in self.tanks:
                                print(f"[DEBUG] Tank '{tank_name}' already exists.")
                            else:
                                self.create_tank(tank_name, dim, persist, max_capacity, single_meta_size, sim_method)
                                print(f"[DEBUG] Tank '{tank_name}' created via create command.")
                        else:
                            print("[ERROR] Insufficient parameters for create command.")
                    except Exception as e:
                        print(f"[ERROR] Failed to process create command: {e}")
                        traceback.print_exc()
                elif command_name == "save":
                    # コマンド例: "save,sample_tank"
                    if len(parts) >= 2:
                        tank_name = parts[1]
                        if tank_name in self.tanks:
                            try:
                                tank = self.tanks[tank_name]
                                tank._read_shared_metadata()
                                tank._parse_params(tank.metadata.get("params", {}))
                                print(f"[DEBUG] Save tank: {str(tank)}")
                                # 保存先パスの作成
                                save_path_npz = os.path.join(self.store_dir, f"{tank_name}.npz")
                                save_path_pkl = os.path.join(self.store_dir, f"{tank_name}.pkl")
                                # ベクトルデータは有効なデータ範囲のみ保存
                                np.savez(save_path_npz, vectors=tank.vectors[:len(tank)])
                                # メタデータ保存
                                with open(save_path_pkl, "wb") as f:
                                    pickle.dump(tank.metadata, f)
                                print(f"[DEBUG] Tank '{tank_name}' saved to files.")
                            except Exception as e:
                                print(f"[ERROR] Failed to save tank '{tank_name}': {e}")
                        else:
                            print(f"[ERROR] Tank '{tank_name}' not found for saving.")
                    else:
                        print("[ERROR] Insufficient parameters for save command.")
                elif command_name == "log":
                    # コマンド例: "log,sample_tank,log_message"
                    if len(parts) >= 3:
                        print(f"[DEBUG] Log command received for tank: {parts[1]} with message: {parts[2]}")
                        tank = self.tanks.get(parts[1])
                        tank._read_shared_metadata()
                        tank._parse_params(tank.metadata.get("params", {}))
                        print(f"[DEBUG] Tank: {str(tank)}")
                # コマンド処理後、共有バッファをクリア（全0に戻す）＝Ack とする
                self._comm_buffer.fill(0)
            time.sleep(0.01)

    def stop_event_loop(self):
        """
        イベントループの終了を要求し、共有メモリを解放する
        """
        self._stop_event.set()
        self._event_thread.join()
        self.close()
        self.unlink()
        self._loop = False

    def close(self):
        for tank in self.tanks.values():
            # タンクの共有メモリを解放
            try:
                tank.shm.close()
                tank.meta_shm.close()
            except Exception:
                pass
        self._comm_shm.close()

    def unlink(self):
        for tank in self.tanks.values():
            # タンクの共有メモリを解放
            try:
                tank.shm.unlink()
                tank.meta_shm.unlink()
            except Exception as e:
                pass
        try:
            self._comm_shm.unlink()
        except FileNotFoundError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # close → unlink の順番で確実に解放
        try:
            self.close()
            if self._loop:
                self.unlink()
                self._loop = False
        except FileNotFoundError:
            # 既に解放済みの場合は無視
            print(f"[ERROR] Failed to dispose tank")
            traceback.print_exc()
            pass
        except Exception:
            pass

    def __del__(self):
        # フォールバックとして __del__ でも close+unlink
        try:
            self.close()
            if self._loop:
                self.unlink()
        except FileNotFoundError:
            # 既に解放済みの場合は無視
            print(f"[ERROR] Failed to dispose tank")
            traceback.print_exc()
            pass
        except Exception:
            pass

# ----------------------------------------------------------------------
# 動作確認用サンプルコード（単体テスト）
# ----------------------------------------------------------------------
if __name__ == '__main__':
    store_dir = "data"
    store_name = "tankstore_comm"
    # 指定した永続化ディレクトリが存在しなければ作成
    if not os.path.exists(store_dir):
        os.makedirs(store_dir)
        print("永続化ディレクトリ '%s' を作成しました。", store_dir)
    
    # TankStore の初期化: store_dir 内の既存タンク（永続化ファイル）を自動復元
    print("共有メモリストアを初期化中 (store_dir=%s, store_name=%s)...", store_dir, store_name)
    with TankStore(store_dir=store_dir, store_name=store_name) as store:
        print(f"TankStore が初期化されました。登録タンク数: {len(store.tanks)}")
        
        # サーバプロセスの待機ループ
        print("サーバプロセスを起動中です。Ctrl+C で停止します。")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("サーバプロセス停止中... イベントループを停止します。")
            # 各タンクの永続化処理（TankStore 側で管理）を実施する場合は、
            # ここで必要に応じた処理（例：tank.save()）を呼び出してください。
            # for tank in store.tanks.values():
            #     if tank.persist:
            #         tank.save()
            #     print(f"Tank '{tank.tank_name}' の永続化処理を実施。")
            # TankStore のイベントループの停止と共有メモリの後片付け
            store.stop_event_loop()
            print("TankStore のイベントループを停止しました。")