"""
【概要】
  本ファイルは、ベクトルの類似度計算に利用する各種関数と、利用可能な計算方式を定義する Enum を含みます。
  
【主な内容】
  - VectorSimMethod: 利用可能な類似度計算方式("inner", "cosine", "euclidean")を定義する Enum クラス
  - calc_inner: 内積による類似度計算関数
  - calc_cosine: コサイン類似度計算関数
  - calc_euclidean: ユークリッド距離に基づく類似度（距離が小さいほど類似度が高い）計算関数
  - SIM_METHODS: 文字列キーと関数を紐付けた辞書
     
【使用例】
  下記サンプルコードでは、複数のベクトルとクエリベクトルを用いて、各種計算関数がどのように動作するかを確認できます。
"""

import numpy as np
from enum import Enum

# ======================================================================
# Enum 定義：VectorSimMethod
# ======================================================================
class VectorSimMethod(Enum):
    # 内積(dot product)を用いた類似度計算
    INNER = "inner"
    # コサイン類似度を用いた計算
    COSINE = "cosine"
    # ユークリッド距離を用いた計算（距離が小さいほど類似度が高いと解釈するため、負の値を返す）
    EUCLIDEAN = "euclidean"

# ======================================================================
# calc_inner: 内積による計算関数
# ======================================================================
def calc_inner(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    """
    内積を利用して、ベクトル集合と1つのクエリベクトル間の類似度スコアを計算します。
    
    引数:
      vectors (np.ndarray): 複数のベクトルを含む配列 (形状：(n, dim))
      query (np.ndarray): 比較対象のクエリベクトル (形状：(dim,))
    
    戻り値:
      各ベクトルとクエリの内積を格納した配列 (形状：(n,))
    """
    return np.dot(vectors, query)

# ======================================================================
# calc_cosine: コサイン類似度計算関数
# ======================================================================
def calc_cosine(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    """
    コサイン類似度を計算します。
    コサイン類似度は、2つのベクトルの方向性の類似度を示し、1に近いほど類似していることを意味します。
    
    引数:
      vectors (np.ndarray): 複数のベクトルが格納された配列 (形状：(n, dim))
      query (np.ndarray): クエリベクトル (形状：(dim,))
    
    戻り値:
      各ベクトルとクエリのコサイン類似度スコアを格納した配列 (形状：(n,))
    """
    # 各ベクトルの L2 ノルム（各行ごと）を計算
    norm_vectors = np.linalg.norm(vectors, axis=1)
    # クエリの L2 ノルムを計算
    norm_query = np.linalg.norm(query)
    # 内積をそれぞれのノルムの積で割ってコサイン類似度を算出
    # ゼロ除算対策として微小な定数 1e-8 を加算
    return np.dot(vectors, query) / (norm_vectors * norm_query + 1e-8)

# ======================================================================
# calc_euclidean: ユークリッド距離に基づく類似度計算関数
# ======================================================================
def calc_euclidean(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    """
    ユークリッド距離を計算し、その負の値を類似度スコアとして返します。
    距離が小さいほど(負の値が大きいほど)類似度が高いと解釈します。
    
    引数:
      vectors (np.ndarray): 複数のベクトルを含む配列 (形状：(n, dim))
      query (np.ndarray): クエリベクトル (形状：(dim,))
    
    戻り値:
      各ベクトルとクエリとのユークリッド距離の負の値を格納した配列 (形状：(n,))
    """
    return -np.linalg.norm(vectors - query, axis=1)

# ======================================================================
# SIM_METHODS 辞書: 類似度計算方式のマッピング
# ======================================================================
SIM_METHODS = {
    "inner": calc_inner,
    "cosine": calc_cosine,
    "euclidean": calc_euclidean,
}

# ======================================================================
# 動作確認用サンプルコード
# ======================================================================
if __name__ == '__main__':
    # サンプルのベクトル集合（例として3次元ベクトルを3個）
    vectors = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float32)
    
    # クエリベクトル（例）
    query = np.array([1.0, 1.0, 0.0], dtype=np.float32)
    
    print("=== 動作確認: 内積による類似度計算 ===")
    inner_scores = calc_inner(vectors, query)
    print("内積スコア:", inner_scores)
    
    print("\n=== 動作確認: コサイン類似度計算 ===")
    cosine_scores = calc_cosine(vectors, query)
    print("コサイン類似度スコア:", cosine_scores)
    
    print("\n=== 動作確認: ユークリッド距離に基づく類似度計算 ===")
    euclidean_scores = calc_euclidean(vectors, query)
    print("ユークリッド距離（負の値）スコア:", euclidean_scores)
    
    # SIM_METHODS 辞書を利用した動作確認
    method = "cosine"  # 計算方式を指定
    if method in SIM_METHODS:
        func = SIM_METHODS[method]
        scores = func(vectors, query)
        print(f"\n[SIM_METHODS] {method} スコア:", scores)