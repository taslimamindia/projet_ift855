import numpy as np
from models.faissmanager import Faiss
from outils.dataset import Data


class FakeIndex:
    def __init__(self, indices):
        # indices: list of indices to return
        self._indices = indices

    def search(self, query_embedding, k=3):
        # return dummy distances and the indices array shape (1, k)
        idxs = np.array([self._indices[:k]])
        dists = np.zeros_like(idxs, dtype=float)
        return dists, idxs


class FakeEmb:
    def __init__(self, vec):
        self._vec = np.array(vec)

    def fireworks_encoding_query(self, query):
        return self._vec


def test_search_similar_documents_and_context():
    data = Data()
    # two chunk embeddings (2-d)
    data.embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
    # map each chunk to a source url
    data.sources = ["url1", "url2"]
    # documents: each url maps to a list of strings (as expected by Faiss.search_similar_context)
    data.documents = {"url1": ["doc1 content"], "url2": ["doc2 content"]}

    fake_emb = FakeEmb([0.1, 0.2])
    faiss_mgr = Faiss(data=data, embeddings=fake_emb)

    # Assign a fake index that will return both indices
    data.index = FakeIndex([0, 1])

    docs = faiss_mgr.search_similar_documents("query", k=2)
    assert isinstance(docs, set)
    assert docs == {"url1", "url2"}

    context, urls = faiss_mgr.search_similar_context("query", k=2)
    assert "doc1 content" in context
    assert "doc2 content" in context
    assert urls == {"url1", "url2"}
