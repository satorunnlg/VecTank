#!/usr/bin/env python3
# examples/run_server.py
from vectank.server import VectorDBServer
from vectank.core import VectorSimMethod
import numpy as np

def main():
    server = VectorDBServer(port=50000, authkey=b'secret', save_file="vectank_data")
    # デフォルトテーブル "default" を作成（1200次元、float32、コサイン類似度）
    server.db.create_table("default", dim=1200, default_sim_method=VectorSimMethod.COSINE, dtype=np.float32)
    server.run()

if __name__ == "__main__":
    main()
