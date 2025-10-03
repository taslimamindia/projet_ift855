import json
import numpy as np
from sentence_transformers import SentenceTransformer


def save_texts_to_json(texts, filename='crawled_data.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(texts, f, ensure_ascii=False, indent=4)

def load_texts_from_json(filename='crawled_data.json'):
    with open(filename, 'r', encoding='utf-8') as f:
        texts = json.load(f)
    return texts

def save_embeddings(embeddings, model, filename):
    model.save("./datasets/embeddings_model")
    np.save(filename, embeddings)

def load_embeddings(filename):
    model = SentenceTransformer(filename + "embeddings_model")
    embeddings = np.load(filename + "embeddings.npy")
    return embeddings, model