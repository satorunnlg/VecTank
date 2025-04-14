# vectank/core.py
import numpy as np
from enum import Enum

class VectorSimMethod(Enum):
    INNER = "inner"
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"

def calc_inner(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    return np.dot(vectors, query)

def calc_cosine(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    norm_vectors = np.linalg.norm(vectors, axis=1)
    norm_query = np.linalg.norm(query)
    return np.dot(vectors, query) / (norm_vectors * norm_query + 1e-8)

def calc_euclidean(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    return -np.linalg.norm(vectors - query, axis=1)

SIM_METHODS = {
    "inner": calc_inner,
    "cosine": calc_cosine,
    "euclidean": calc_euclidean,
}
