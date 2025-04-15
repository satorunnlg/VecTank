# vectank/core.py
import numpy as np  # 数値計算ライブラリ NumPy をインポート
from enum import Enum  # Enum クラスを利用して、定数の集まりを定義するためにインポート

# VectorSimMethod クラスは、利用可能な類似度計算方法を定義する Enum です。
class VectorSimMethod(Enum):
    # 内積（dot product）を用いた類似度計算
    INNER = "inner"
    # コサイン類似度（cosine similarity）を用いた類似度計算
    COSINE = "cosine"
    # ユークリッド距離（euclidean distance）を用いた類似度計算（距離が小さいほど類似度が高い）
    EUCLIDEAN = "euclidean"

# calc_inner 関数は、ベクトル集合とクエリベクトル間の内積を計算します。
#
# 引数:
#   vectors (np.ndarray): 複数のベクトルを含む NumPy 配列 (形状は (n, dim) など)
#   query (np.ndarray): 比較対象の1つのクエリベクトル (形状は (dim,) など)
#
# 戻り値:
#   各ベクトルとの内積を表す NumPy 配列
def calc_inner(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    return np.dot(vectors, query)

# calc_cosine 関数は、ベクトル集合とクエリベクトル間のコサイン類似度を計算します。
#
# コサイン類似度は、2つのベクトルの方向の類似度を示し、1に近い値ほど類似していることを意味します。
#
# 引数:
#   vectors (np.ndarray): 複数のベクトルの集合
#   query (np.ndarray): コサイン類似度を計算するための1つのクエリベクトル
#
# 戻り値:
#   各ベクトルとのコサイン類似度を計算した結果の NumPy 配列
def calc_cosine(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    # 各ベクトルの L2 ノルムを計算 (各行ごとに)
    norm_vectors = np.linalg.norm(vectors, axis=1)
    # クエリベクトルの L2 ノルムを計算
    norm_query = np.linalg.norm(query)
    # 内積をノルムの積で割ることで、コサイン類似度を算出
    # 分母がゼロにならないように微小な定数 1e-8 を加算
    return np.dot(vectors, query) / (norm_vectors * norm_query + 1e-8)

# calc_euclidean 関数は、ベクトル集合とクエリベクトル間のユークリッド距離に基づく類似度を計算します。
#
# ユークリッド距離は距離が小さいほど類似しているとみなすため、
# 本実装では距離にマイナスを掛けることで、スコアが大きいほど類似度が高い形に変換しています。
#
# 引数:
#   vectors (np.ndarray): 複数のベクトルの集合
#   query (np.ndarray): 比較対象のクエリベクトル
#
# 戻り値:
#   各ベクトルとの距離 (負の値) を計算した NumPy 配列
def calc_euclidean(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    return -np.linalg.norm(vectors - query, axis=1)

# SIM_METHODS は文字列のキーに対して対応する類似度計算関数を紐付けた辞書です。
# これにより文字列から直接関数を呼び出して計算が可能となります。
SIM_METHODS = {
    "inner": calc_inner,
    "cosine": calc_cosine,
    "euclidean": calc_euclidean,
}
