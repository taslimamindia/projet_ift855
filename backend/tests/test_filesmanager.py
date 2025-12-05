import json
import numpy as np
from pathlib import Path
from outils.filesmanager import FileManager
from outils.dataset import Data


def test_save_and_load_texts(tmp_path):
    data = Data()
    fm = FileManager(data)

    texts = {"https://a": "Hello world", "https://b": "Another text"}
    file_path = tmp_path / "test_texts.json"

    fm.save_texts_to_json(texts, filename=str(file_path))

    loaded = fm.load_texts_from_json(filename=str(file_path))
    assert loaded == texts


def test_save_and_load_embeddings(tmp_path):
    data = Data()
    fm = FileManager(data)

    arr = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    data.embeddings = arr

    folder = str(tmp_path) + "/"
    fm.save_embeddings(folder)

    # clear then load
    data.embeddings = None
    fm.load_embeddings(folder)

    assert np.array_equal(data.embeddings, arr)
