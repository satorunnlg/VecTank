import time
import numpy as np
from vectank.tank import VecTank

def benchmark():
    tank = VecTank("benchmark_tank")
    num_vectors = 10000
    dimension = 128
    vectors = np.random.rand(num_vectors, dimension)
    
    start = time.time()
    for vec in vectors:
        tank.add_vector(vec)
    elapsed = time.time() - start
    print(f"Added {num_vectors} vectors in {elapsed:.4f} seconds")
    
    # ランダムなクエリに対する検索テスト
    query = np.random.rand(dimension)
    start = time.time()
    results = tank.search(query)
    elapsed_search = time.time() - start
    print(f"Search completed in {elapsed_search:.6f} seconds")
    print("Top matching vector indices:", results)

if __name__ == '__main__':
    benchmark()