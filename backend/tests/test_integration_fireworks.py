import os
import pytest
from types import SimpleNamespace


@pytest.mark.integration
def test_fireworks_llm_generate_QA(fireworks_api_key):
    """Integration test: call the real Fireworks LLM generate_QA.

    This test runs only when FIREWORKS_API_KEY is set in the environment.
    It verifies that the LLM instantiation and a simple chat completion succeed.
    """
    if not fireworks_api_key:
        pytest.skip("FIREWORKS_API_KEY not set; skipping integration test")

    from models.LLM import Fireworks_LLM

    data = SimpleNamespace(fireworks_api_key=fireworks_api_key)
    fw = Fireworks_LLM(data)
    res = fw.generate_QA("Say hello in a short sentence.")
    assert isinstance(res, str)
    assert len(res) > 0


@pytest.mark.integration
def test_fireworks_embeddings_encoding(fireworks_api_key):
    """Integration test: call fireworks embedding encoding for a short query."""
    if not fireworks_api_key:
        pytest.skip("FIREWORKS_API_KEY not set; skipping integration test")

    from models.embeddings import Embeddings
    from outils.dataset import Data

    data = Data()
    data.fireworks_api_key = fireworks_api_key
    emb = Embeddings(data)

    vec = emb.fireworks_encoding_query("hello world")
    # Expect a sequence of floats
    assert hasattr(vec, "__len__")
    assert len(vec) > 0
