#!/usr/bin/env python3
# examples/run_server.py
#
# このスクリプトは、TankServer（旧 VectorDBServer）を起動するサンプルです。
# サーバ起動時に、デフォルトタンク "default" を生成（1200次元、float32、コサイン類似度）し、
# リモートクライアントからのタンク操作を受け付けます。

from vectank.server import TankServer  # TankServer クラスをインポート（旧 VectorDBServer）
from vectank.core import VectorSimMethod  # 類似度計算方式 Enum をインポート
import numpy as np  # 高速数値計算用に NumPy をインポート

def main():
    # TankServer のインスタンスを生成
    # port: サーバがリッスンするポート番号 (デフォルト: 50000)
    # authkey: 認証用に利用するバイト列 (ここでは "secret" をバイト列に変換)
    # save_file: 永続化時に利用するファイル名のプレフィックス
    server = TankServer(port=50000, authkey=b'secret', save_file="vectank_data")
    
    # デフォルトタンク "default" を作成
    # ・タンク名: "default"
    # ・dim: タンク内のベクトルの次元数（この例では 1200）
    # ・default_sim_method: 類似度計算方法として、VectorSimMethod.COSINE（コサイン類似度）を指定
    # ・dtype: ベクトルのデータ型として、NumPy の float32 を使用
    server.store.create_tank("default", dim=1200, default_sim_method=VectorSimMethod.COSINE, dtype=np.float32)
    
    # サーバを起動します。
    # server.run() はブロッキング呼び出しとなり、サーバが停止するまで処理が継続されます。
    server.run()

if __name__ == "__main__":
    main()
