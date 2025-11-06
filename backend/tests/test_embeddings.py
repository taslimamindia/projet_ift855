from outils.dataset import Data
from models.embeddings import Embeddings


def test_chunking_and_flatten():
    # Create a document long enough to create multiple chunks
    long_text = "A" * 1200
    data = Data()
    data.documents = {"https://example.com": long_text}

    emb = Embeddings(data)
    # use smaller chunk size to speed the test
    emb.chunking(chunk_size=500, overlap=50)

    # After chunking we should have lists of chunks and corresponding sources
    assert isinstance(data.chunks, list)
    assert isinstance(data.sources, list)
    assert len(data.chunks) == len(data.sources)
    assert len(data.chunks[0]) >= 2

    # Now flatten and check shapes
    emb.flat_chunks_and_sources()
    assert isinstance(data.chunks, list)
    assert isinstance(data.sources, list)
    assert len(data.chunks) == len(data.sources)
