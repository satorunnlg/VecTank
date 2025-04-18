# vectank/tank.py
import numpy as np  # 数値計算ライブラリ NumPy をインポート
import threading    # 複数のスレッドからの同時アクセスを防ぐためのロック機構を提供
import pickle       # オブジェクトの永続化（シリアライズ／デシリアライズ）に利用
import os           # ファイルやパスの操作に利用
from .core import VectorSimMethod, SIM_METHODS  # 類似度計算方法の Enum と、各計算関数の辞書をインポート

# VectorTank クラスは、ベクトルとそれに紐付くメタデータを管理するタンクを表現します。
class VectorTank:
    def __init__(self, tank_name: str, dim: int,
                 default_sim_method: VectorSimMethod,
                 dtype: np.dtype, persist: bool = False, file_path: str = None):
        self.tank_name = tank_name
        self.dim = dim
        self.default_sim_method = default_sim_method
        self.dtype = dtype
        self.persist = persist
        if self.persist:
            if file_path is None:
                self.persistence_path = os.path.join(os.getcwd(), self.tank_name)
            else:
                self.persistence_path = file_path
        else:
            self.persistence_path = None
        self._lock = threading.Lock()
        self._vectors = np.empty((0, dim), dtype=dtype)
        self._metadata = {}
        self._key_to_index = {}
        self._auto_id = 0

        if self.persist:
            self.load_from_file()
    
    def __getstate__(self):
        """
        オブジェクトのシリアライズ時に呼び出される。
        threading.Lock はシリアライズできないため、状態から削除して返す。
        """
        state = self.__dict__.copy()
        if '_lock' in state:
            del state['_lock']
        return state

    def __setstate__(self, state):
        """
        オブジェクトのデシリアライズ時に呼び出される。
        ロックを再生成して、デシリアライズ後のオブジェクトを初期化する。
        """
        self.__dict__.update(state)
        self._lock = threading.Lock()

    def __len__(self):
        """テーブルに登録されている全データ件数を返す。"""
        with self._lock:
            return len(self._metadata)

    def _generate_key(self) -> str:
        """
        新しいベクトル追加時に、自動採番で一意なキーを生成する。
        
        戻り値:
          自動生成された一意な文字列キー
        """
        self._auto_id += 1
        return str(self._auto_id)

    def add_vector(self, vector: np.ndarray, metadata: dict, key: str = None) -> str:
        """
        単一のベクトルと付随するメタデータをタンクに追加する。

        引数:
          vector (np.ndarray): 追加するベクトル (形状は (dim,) である必要がある)
          metadata (dict): ベクトルに関連付けるメタデータ
          key (str, オプション): ベクトルに対する一意なキー。指定されなければ自動採番される

        戻り値:
          使用されたキー (自動生成または指定されたキー)

        例外:
          - キーが重複している場合、ValueError を送出
          - ベクトルの次元が想定と異なる場合、ValueError を送出
        """
        with self._lock:
            # キーが指定されていなければ、自動的に生成
            if key is None:
                key = self._generate_key()
            else:
                key = str(key)
            # 同じキーが既に存在する場合はエラーを送出
            if key in self._key_to_index:
                raise ValueError(f"キー {key} は既に存在しています。")
            # ベクトルの形状チェック。次元が一致しなければエラー
            if vector.shape != (self.dim,):
                raise ValueError(f"ベクトルの次元は ({self.dim},) である必要があります。")
            # 1次元のベクトルを 2次元 (1, dim) に変形
            vector_reshaped = vector.reshape(1, self.dim)
            # 既存のベクトル配列が空の場合、新たに設定。そうでなければ連結
            if self._vectors.size == 0:
                self._vectors = vector_reshaped
            else:
                self._vectors = np.concatenate([self._vectors, vector_reshaped], axis=0)
            # 新しく追加したベクトルのインデックスを取得
            new_index = self._vectors.shape[0] - 1
            # キーとインデックスの対応を登録
            self._key_to_index[key] = new_index
            # メタデータもキーに紐付けて登録
            self._metadata[key] = metadata
            return key

    def add_vectors(self, vectors: np.ndarray, metadata_list: list, keys: list = None) -> list:
        """
        複数のベクトルと対応するメタデータを一括追加する。

        引数:
          vectors (np.ndarray): ベクトル群 (形状は (n, dim) である必要がある)
          metadata_list (list): 各ベクトルに対応するメタデータのリスト (長さは n)
          keys (list, オプション): 各ベクトルに対するキーのリスト。指定される場合は長さ n に一致すること

        戻り値:
          追加された各ベクトルに対応するキーのリスト

        例外:
          - 入力の次元またはリストの長さが条件に満たない場合、ValueError を送出
          - キーが重複している場合、ValueError を送出
        """
        with self._lock:
            if vectors.ndim != 2 or vectors.shape[1] != self.dim:
                raise ValueError(f"入力ベクトルは形状 (n, {self.dim}) である必要があります。")
            n = vectors.shape[0]
            if len(metadata_list) != n:
                raise ValueError("metadata_list の長さは追加するベクトル数と一致する必要があります。")
            if keys is not None and len(keys) != n:
                raise ValueError("keys が指定されている場合、長さはベクトル数と一致する必要があります。")
            new_keys = []
            # 各ベクトルに対してキーを生成または指定されたキーを確認
            for i in range(n):
                if keys is None:
                    key = self._generate_key()
                else:
                    key = str(keys[i])
                if key in self._key_to_index:
                    raise ValueError(f"キー {key} は既に存在しています。")
                new_keys.append(key)
            # ベクトル群の追加。初回ならコピー、既存なら連結する
            if self._vectors.size == 0:
                self._vectors = vectors.copy()
            else:
                self._vectors = np.concatenate([self._vectors, vectors], axis=0)
            # 現在のベクトル数から新たに追加される前のカウントを取得
            old_count = self._vectors.shape[0] - n
            # 各ベクトルに対してキーとメタデータを登録
            for i, key in enumerate(new_keys):
                index = old_count + i
                self._key_to_index[key] = index
                self._metadata[key] = metadata_list[i]
            return new_keys

    def search(self, query_vector: np.ndarray, top_k: int, sim_method = None):
        """
        指定されたクエリベクトルに対して類似度検索を行い、上位 top_k 件の結果を返します。

        引数:
          query_vector (np.ndarray): 検索用のクエリベクトル (形状は (dim,) である必要がある)
          top_k (int): 返す上位の件数
          sim_method (オプション): 利用する類似度計算方法 (指定しなければデフォルトを利用)

        戻り値:
          (キー, 類似度スコア, ベクトル, メタデータ) のタプルのリスト

        例外:
          - クエリベクトルの次元が一致しなかった場合、ValueError を送出
          - 指定された類似度計算方式が未対応の場合、ValueError を送出
        """
        with self._lock:
            if query_vector.shape != (self.dim,):
                raise ValueError(f"クエリベクトルの次元は ({self.dim},) である必要があります。")
            # 利用する類似度計算方式を決定 (指定がなければデフォルト)
            method = sim_method if sim_method is not None else self.default_sim_method
            # method が Enum なら .value で文字列を取得、文字列なら小文字化して利用
            if hasattr(method, "value"):
                method_key = method.value
            elif isinstance(method, str):
                method_key = method.lower()
            else:
                raise ValueError("類似度計算方式は Enum または文字列で指定してください。")
            # 指定された類似度計算方式に対応する関数が存在するかチェック
            if method_key not in SIM_METHODS:
                raise ValueError(f"未対応の類似度計算方式です: {method}")
            # 対応する計算関数を取得
            calc_func = SIM_METHODS[method_key]
            # 全ベクトルとクエリベクトルとの類似度スコアを計算
            scores = calc_func(self._vectors, query_vector)
            # 上位 top_k 件の結果を抽出
            if top_k >= scores.shape[0]:
                top_indices = np.argsort(-scores)
            else:
                # argpartition でトップ k 番目までを一度抽出し、そこからスコア順に並べ替え
                top_indices = np.argpartition(-scores, top_k)[:top_k]
                top_indices = top_indices[np.argsort(-scores[top_indices])]
            # インデックスからキーへの変換用辞書を作成
            index_to_key = {index: k for k, index in self._key_to_index.items()}
            results = []
            # 上位結果からキー、スコア、メタデータ、ベクトルを抽出
            for idx in top_indices:
                key = index_to_key.get(idx)
                if key is not None:
                    results.append((key, float(scores[idx]), self._vectors[idx], self._metadata.get(key)))
            return results

    def update_vector(self, key: str, new_vector: np.ndarray, new_metadata: dict = None):
        """
        指定されたキーに対応するベクトルを更新する。
        
        引数:
          key (str): 更新対象のベクトルのキー
          new_vector (np.ndarray): 新しいベクトル (形状は (dim,) である必要がある)
          new_metadata (dict, オプション): 新しいメタデータ（指定されていれば更新）

        例外:
          - キーが存在しない場合、KeyError を送出
          - ベクトルの次元が一致しない場合、ValueError を送出
        """
        with self._lock:
            if key not in self._key_to_index:
                raise KeyError(f"キー {key} は存在しません。")
            if new_vector.shape != (self.dim,):
                raise ValueError(f"新しいベクトルの次元は ({self.dim},) である必要があります。")
            # キーに対応するインデックスを取得して更新
            index = self._key_to_index[key]
            self._vectors[index, :] = new_vector
            # 新たにメタデータが指定された場合、更新
            if new_metadata is not None:
                self._metadata[key] = new_metadata

    def filter_by_metadata(self, conditions=None) -> list:
        """
        メタデータに基づいてキーをフィルタリングします。

        パラメータ conditions には以下のいずれかを指定できます:
         - 辞書形式の場合:
             各 metadata の値が、辞書に記載されたキーと一致する場合に True と判断します。
             例: {"map_file": "room-layout.svg"} なら metadata["map_file"] == "room-layout.svg" をチェック。
         - コールバック関数の場合:
             条件判定用の関数を渡すと、各 metadata をその関数に渡して True を返すアイテムをフィルタします。
             例: lambda meta: meta.get("score", 0) >= 50

        :param conditions: 辞書 または callable を指定
        :return: 条件に合致するアイテムのキーのリスト
        :raises TypeError: conditions が辞書でもコールバックでもない場合
        """
        with self._lock:
            if conditions is None:
                return []
            if callable(conditions):
                # コールバック関数として評価
                return [key for key, meta in self._metadata.items() if conditions(meta)]
            elif isinstance(conditions, dict):
                # 辞書に基づく単純等価比較
                return [key for key, meta in self._metadata.items()
                        if all(meta.get(k) == v for k, v in conditions.items())]
            else:
                raise TypeError("conditions には辞書または callable を指定してください。")

    def delete(self, key: str):
        """
        指定されたキーに対応するベクトルとそのメタデータを削除する。

        引数:
          key (str): 削除する対象のベクトルのキー

        例外:
          - キーが存在しない場合、KeyError を送出
        """
        with self._lock:
            if key not in self._key_to_index:
                raise KeyError(f"キー {key} は存在しません。")
            # 削除対象のインデックスを取得
            del_index = self._key_to_index[key]
            # NumPy の delete を利用して、対象の行を削除
            self._vectors = np.delete(self._vectors, del_index, axis=0)
            # メタデータおよびキー-インデックスの対応から削除
            del self._metadata[key]
            del self._key_to_index[key]
            # インデックスの再構築: 削除によりシフトするため、全体を更新
            new_mapping = {}
            for new_index, existing_key in enumerate(self._key_to_index.keys()):
                new_mapping[existing_key] = new_index
            self._key_to_index = new_mapping

    def delete_keys(self, keys: list) -> list:
        """
        渡されたキー一覧に対して、一括で削除を実施します。
        _vectors から該当行をまとめて削除し、_metadata および _key_to_index の状態を再構築します。
        
        :param keys: 削除対象のキーのリスト
        :return: 実際に削除されたキーのリスト
        """
        with self._lock:
            # 有効なキーのみ抽出
            valid_keys = [key for key in keys if key in self._metadata]
            if not valid_keys:
                return []
            
            # 削除する各キーに対応するインデックスを取得
            indices_to_delete = [self._key_to_index[key] for key in valid_keys]
            # 削除時にインデックスのずれが起こらないよう、降順にソート
            sorted_indices = sorted(indices_to_delete, reverse=True)
            
            # np.delete を使って _vectors から該当行を一括削除
            self._vectors = np.delete(self._vectors, sorted_indices, axis=0)
            
            # _metadata と _key_to_index から対象キーを削除
            for key in valid_keys:
                del self._metadata[key]
                del self._key_to_index[key]
            
            # 残ったアイテムの順序が _vectors の行順と合致するよう、_key_to_index を再構築
            new_mapping = {}
            for new_index, key in enumerate(list(self._key_to_index.keys())):
                new_mapping[key] = new_index
            self._key_to_index = new_mapping
            
            return valid_keys

    def clear(self):
        """
        タンク内のすべてのベクトル、メタデータ、キー対応情報を初期化する。
        自動採番用のカウンタもリセットする。
        """
        with self._lock:
            # 空の配列にしてベクトルをリセット
            self._vectors = np.empty((0, self.dim), dtype=self.dtype)
            # メタデータとキーの対応情報をクリア
            self._metadata.clear()
            self._key_to_index.clear()
            self._auto_id = 0

    def save_to_file(self):
        """
        データ永続化用に、ベクトルとメタデータをファイルに保存する。
        
        保存するファイル:
          - ベクトル情報は NumPy の npz 形式で保存
          - メタデータ、キー、採番カウンタは pickle 形式で保存
          
        ※ persist フラグが False の場合は何も行わない。
        """
        if not self.persist:
            return
        with self._lock:
            # 保存ファイル名は persistence_path と tank_name を連結して決定
            vectors_file = f"{self.persistence_path}_{self.tank_name}_vectors.npz"
            # NumPy 形式でベクトル群を保存
            np.savez(vectors_file, vectors=self._vectors)
            # メタデータ関連情報をまとめた辞書を作成
            meta_data = {
                "metadata": self._metadata,
                "key_to_index": self._key_to_index,
                "auto_id": self._auto_id
            }
            meta_file = f"{self.persistence_path}_{self.tank_name}_meta.pkl"
            # pickle を利用してメタデータを保存
            with open(meta_file, "wb") as f:
                pickle.dump(meta_data, f)

    def load_from_file(self):
        """
        永続化フラグが有効な場合、既存の永続化ファイルから、ベクトルとメタデータをロードする。

        処理内容:
          - 該当するベクトルファイルとメタデータファイルが存在するか確認し、
            存在する場合にそれらを読み込む。
        """
        if not self.persist:
            return
        vectors_file = f"{self.persistence_path}_{self.tank_name}_vectors.npz"
        meta_file = f"{self.persistence_path}_{self.tank_name}_meta.pkl"
        # 両方のファイルが存在しなければ何もしない
        if not os.path.exists(vectors_file) or not os.path.exists(meta_file):
            return
        with self._lock:
            # NumPy 形式のファイルからベクトル群をロード
            data = np.load(vectors_file)
            self._vectors = data["vectors"]
            # pickle 形式のファイルからメタデータ等をロード
            with open(meta_file, "rb") as f:
                meta_data = pickle.load(f)
                self._metadata = meta_data.get("metadata", {})
                self._key_to_index = meta_data.get("key_to_index", {})
                self._auto_id = meta_data.get("auto_id", 0)
