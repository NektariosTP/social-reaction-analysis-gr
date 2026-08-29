import numpy as np
from nlp.embeddings import embed_query


def test_embed_query_returns_unit_vector():
    vec = embed_query("Πανελλαδική απεργία στη Θεσσαλονίκη")
    assert vec.shape == (768,)
    assert vec.dtype == np.float32
    assert abs(float(np.linalg.norm(vec)) - 1.0) < 1e-3
