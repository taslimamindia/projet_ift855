import faiss
import numpy as np
from outils.dataset import Data
from .embeddings import Embeddings

class Faiss:
    def __init__(self, data:Data, embeddings:Embeddings):
        self.data = data
        self.embeddings = embeddings


    def create_faiss_index(self):
        """Create a FAISS index for embeddings and add vectors to it.

        The method expects `self.data.embeddings` to be a 2D numpy array of shape (n_vectors, dim).
        After creation, the index is stored in `self.data.index`.
        """

        dimension = self.data.embeddings.shape[1]
        self.data.index = faiss.IndexFlatL2(dimension)
        self.data.index.add(np.array(self.data.embeddings))


    def search_similar_context(self, query, k=3):
        """Retrieve the most relevant context for a given query.

        Args:
            query (str): User query text.
            k (int, optional): Number of most similar documents to retrieve. Defaults to 3.

        Returns:
            tuple: (context_text, indices_set)
                - context_text (str): Concatenated text of the selected relevant contexts.
                - indices_set (set): Set of source URLs corresponding to the retrieved contexts.
        """

        query_embedding = np.array(self.embeddings.fireworks_encoding_query(query))
        query_embedding = query_embedding.reshape((1, query_embedding.shape[0]))
        _, indices = self.data.index.search(query_embedding, k=k)
        indices_documents = set([self.data.sources[i] for i in indices[0]])
        context_selected = " ".join([" ".join(self.data.documents[index]) for index in indices_documents])

        return context_selected, indices_documents
    
    def search_similar_documents(self, query, k=3):
        """Retrieve the most relevant context for a given query.

        Args:
            query (str): User query text.
            k (int, optional): Number of most similar documents to retrieve. Defaults to 3.

        Returns:
            set: Set of source URLs corresponding to the retrieved contexts.
        """

        query_embedding = np.array(self.embeddings.fireworks_encoding_query(query))
        query_embedding = query_embedding.reshape((1, query_embedding.shape[0]))
        _, indices = self.data.index.search(query_embedding, k=k)
        indices_documents = set([self.data.sources[i] for i in indices[0]])

        return indices_documents