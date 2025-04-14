# vectank/table.py
import numpy as np
import threading
import pickle
import os
from .core import VectorSimMethod, SIM_METHODS

class VectorTable:
    def __init__(self, table_name: str, dim: int,
                 default_sim_method: VectorSimMethod,
                 dtype: np.dtype, save_file: str = None):
        self.table_name = table_name
        self.dim = dim
        self.default_sim_method = default_sim_method
        self.dtype = dtype
        self.save_file = save_file

        self._lock = threading.Lock()
        self._vectors = np.empty((0, dim), dtype=dtype)
        self._metadata = {}
        self._key_to_index = {}
        self._auto_id = 0

    def __getstate__(self):
        state = self.__dict__.copy()
        if '_lock' in state:
            del state['_lock']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = threading.Lock()

    def _generate_key(self) -> str:
        self._auto_id += 1
        return str(self._auto_id)

    def add_vector(self, vector: np.ndarray, metadata: dict, key: str = None) -> str:
        with self._lock:
            if key is None:
                key = self._generate_key()
            else:
                key = str(key)
            if key in self._key_to_index:
                raise ValueError(f"キー {key} は既に存在しています。")
            if vector.shape != (self.dim,):
                raise ValueError(f"ベクトルの次元は ({self.dim},) である必要があります。")
            vector_reshaped = vector.reshape(1, self.dim)
            if self._vectors.size == 0:
                self._vectors = vector_reshaped
            else:
                self._vectors = np.concatenate([self._vectors, vector_reshaped], axis=0)
            new_index = self._vectors.shape[0] - 1
            self._key_to_index[key] = new_index
            self._metadata[key] = metadata
            return key

    def add_vectors(self, vectors: np.ndarray, metadata_list: list, keys: list = None) -> list:
        with self._lock:
            if vectors.ndim != 2 or vectors.shape[1] != self.dim:
                raise ValueError(f"入力ベクトルは形状 (n, {self.dim}) である必要があります。")
            n = vectors.shape[0]
            if len(metadata_list) != n:
                raise ValueError("metadata_list の長さは追加するベクトル数と一致する必要があります。")
            if keys is not None and len(keys) != n:
                raise ValueError("keys が指定されている場合、長さはベクトル数と一致する必要があります。")
            new_keys = []
            for i in range(n):
                if keys is None:
                    key = self._generate_key()
                else:
                    key = str(keys[i])
                if key in self._key_to_index:
                    raise ValueError(f"キー {key} は既に存在しています。")
                new_keys.append(key)
            if self._vectors.size == 0:
                self._vectors = vectors.copy()
            else:
                self._vectors = np.concatenate([self._vectors, vectors], axis=0)
            old_count = self._vectors.shape[0] - n
            for i, key in enumerate(new_keys):
                index = old_count + i
                self._key_to_index[key] = index
                self._metadata[key] = metadata_list[i]
            return new_keys

    def search(self, query_vector: np.ndarray, top_k: int, sim_method = None):
        with self._lock:
            if query_vector.shape != (self.dim,):
                raise ValueError(f"クエリベクトルの次元は ({self.dim},) である必要があります。")
            method = sim_method if sim_method is not None else self.default_sim_method
            if hasattr(method, "value"):
                method_key = method.value
            elif isinstance(method, str):
                method_key = method.lower()
            else:
                raise ValueError("類似度計算方式は Enum または文字列で指定してください。")
            if method_key not in SIM_METHODS:
                raise ValueError(f"未対応の類似度計算方式です: {method}")
            calc_func = SIM_METHODS[method_key]
            scores = calc_func(self._vectors, query_vector)
            if top_k >= scores.shape[0]:
                top_indices = np.argsort(-scores)
            else:
                top_indices = np.argpartition(-scores, top_k)[:top_k]
                top_indices = top_indices[np.argsort(-scores[top_indices])]
            index_to_key = {index: k for k, index in self._key_to_index.items()}
            results = []
            for idx in top_indices:
                key = index_to_key.get(idx)
                if key is not None:
                    results.append((key, float(scores[idx]), self._metadata.get(key)))
            return results

    def update_vector(self, key: str, new_vector: np.ndarray, new_metadata: dict = None):
        with self._lock:
            if key not in self._key_to_index:
                raise KeyError(f"キー {key} は存在しません。")
            if new_vector.shape != (self.dim,):
                raise ValueError(f"新しいベクトルの次元は ({self.dim},) である必要があります。")
            index = self._key_to_index[key]
            self._vectors[index, :] = new_vector
            if new_metadata is not None:
                self._metadata[key] = new_metadata

    def delete(self, key: str):
        with self._lock:
            if key not in self._key_to_index:
                raise KeyError(f"キー {key} は存在しません。")
            del_index = self._key_to_index[key]
            self._vectors = np.delete(self._vectors, del_index, axis=0)
            del self._metadata[key]
            del self._key_to_index[key]
            new_mapping = {}
            for new_index, existing_key in enumerate(self._key_to_index.keys()):
                new_mapping[existing_key] = new_index
            self._key_to_index = new_mapping

    def clear(self):
        with self._lock:
            self._vectors = np.empty((0, self.dim), dtype=self.dtype)
            self._metadata.clear()
            self._key_to_index.clear()
            self._auto_id = 0

    def save_to_file(self):
        if self.save_file is None:
            return
        with self._lock:
            vectors_file = f"{self.save_file}_{self.table_name}_vectors.npz"
            np.savez(vectors_file, vectors=self._vectors)
            meta_data = {
                "metadata": self._metadata,
                "key_to_index": self._key_to_index,
                "auto_id": self._auto_id
            }
            meta_file = f"{self.save_file}_{self.table_name}_meta.pkl"
            with open(meta_file, "wb") as f:
                pickle.dump(meta_data, f)

    def load_from_file(self):
        if self.save_file is None:
            return
        vectors_file = f"{self.save_file}_{self.table_name}_vectors.npz"
        meta_file = f"{self.save_file}_{self.table_name}_meta.pkl"
        if not os.path.exists(vectors_file) or not os.path.exists(meta_file):
            return
        with self._lock:
            data = np.load(vectors_file)
            self._vectors = data["vectors"]
            with open(meta_file, "rb") as f:
                meta_data = pickle.load(f)
                self._metadata = meta_data.get("metadata", {})
                self._key_to_index = meta_data.get("key_to_index", {})
                self._auto_id = meta_data.get("auto_id", 0)
