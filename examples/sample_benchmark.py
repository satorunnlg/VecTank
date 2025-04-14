#!/usr/bin/env python3
# examples/sample_benchmark.py
import numpy as np
import time
from vectank.client import VectorDBClient
from vectank.core import VectorSimMethod

def main():
    client = VectorDBClient()
    table = client.get_table("default")
    dim = 1200
    num_vectors = 20000
    top_k = 100

    vectors = np.random.rand(num_vectors, dim).astype(np.float32)
    metadata_list = [{"index": i} for i in range(num_vectors)]

    start_time = time.time()
    keys = table.add_vectors(vectors, metadata_list)
    end_time = time.time()
    elapsed_ms = (end_time - start_time) * 1000
    print(f"{num_vectors} 個のベクトル登録にかかった時間: {elapsed_ms:.2f} ms")

    query_vector = np.random.rand(dim).astype(np.float32)
    start_search = time.time()
    results = table.search(query_vector, top_k=top_k)
    end_search = time.time()
    elapsed_search_ms = (end_search - start_search) * 1000
    print(f"上位 {top_k} 件の検索にかかった時間: {elapsed_search_ms:.2f} ms")
    print("検索結果の先頭 5 件:")
    for res in results[:5]:
        print(res)

if __name__ == "__main__":
    main()
