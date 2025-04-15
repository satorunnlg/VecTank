#!/usr/bin/env python3
# examples/sample_benchmark.py
#
# このスクリプトは、TankClient を利用してリモートストアに接続し、
# デフォルトタンク "default" に対する大量のベクトルの一括登録と、
# 類似度検索のパフォーマンスを測定するサンプルです。
#
# ・ベクトルの次元数は 1200
# ・登録するベクトル数は 20,000 件
# ・検索結果として上位 100 件を取得
#
# 各処理の実行時間を計測し、速度評価に役立てることができます。

import numpy as np
import time
from vectank.client import TankClient  # 旧 VectorDBClient → TankClient に名称統一
from vectank.core import VectorSimMethod

def main():
    # TankClient のインスタンスを生成し、リモートストアへ接続する。
    client = TankClient()
    
    # リモートストアから "default" タンクを取得する。
    # ※ タンクは、データの登録や検索の単位となるコンテナです。
    tank = client.get_tank("default")
    
    # ベクトルの次元数、登録件数および検索結果の件数を定義
    dim = 1200            # 各ベクトルの持つ要素数（次元数）
    num_vectors = 20000   # 登録するベクトルの総数
    top_k = 100           # 検索結果として返す上位の件数

    # 登録用の乱数ベクトル群を生成
    # ・np.random.rand() により 0~1 の一様分布乱数からベクトルを生成し、float32 型にキャスト
    vectors = np.random.rand(num_vectors, dim).astype(np.float32)
    
    # 各ベクトルに対して、簡単なメタデータとしてインデックス番号を設定
    metadata_list = [{"index": i} for i in range(num_vectors)]
    
    # ここから一括登録処理の実行時間を計測
    start_time = time.time()
    # Tank の add_vectors() メソッドを用いて、複数のベクトルと対応するメタデータを一括登録する
    keys = tank.add_vectors(vectors, metadata_list)
    end_time = time.time()
    elapsed_ms = (end_time - start_time) * 1000
    print(f"{num_vectors} 個のベクトル登録にかかった時間: {elapsed_ms:.2f} ms")
    
    # 検索処理に使用するクエリベクトルをランダムに生成
    query_vector = np.random.rand(dim).astype(np.float32)
    
    # 類似度検索の実行時間を計測
    start_search = time.time()
    # Tank の search() メソッドで、クエリベクトルとの類似度を計算し、上位 top_k 件の結果を取得
    results = tank.search(query_vector, top_k=top_k)
    end_search = time.time()
    elapsed_search_ms = (end_search - start_search) * 1000
    print(f"上位 {top_k} 件の検索にかかった時間: {elapsed_search_ms:.2f} ms")
    
    # 検索結果の先頭 5 件を画面に出力して確認
    print("検索結果の先頭 5 件:")
    for res in results[:5]:
        print(res)

if __name__ == "__main__":
    main()
