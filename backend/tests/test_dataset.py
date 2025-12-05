import numpy as np
from outils.dataset import Data


def test_data_defaults():
    d = Data()
    assert d.documents is None
    assert d.chunks is None
    assert d.sources is None
    assert d.embeddings is None
    assert d.index is None
    assert d.fireworks_api_key is None


def test_data_can_hold_embeddings():
    d = Data()
    d.embeddings = np.array([[1.0, 2.0], [3.0, 4.0]])
    assert d.embeddings.shape == (2, 2)
