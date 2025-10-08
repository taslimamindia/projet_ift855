import faiss
import numpy as np
from outils.dataset import Data

class Faiss:
    def __init__(self, data:Data):
        self.data = data


    def create_faiss_index(self):
        """Create a FAISS index for embeddings.
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
            tuple:
                - str: Concatenated text of the selected relevant contexts.
                - set: Set of document indices corresponding to the retrieved contexts.
        """

        query_embedding = self.data.model.encode([query])
        _, indices = self.data.index.search(np.array(query_embedding), k=k)
        indices_documents = set([self.data.sources[i] for i in indices[0]])
        context_selected = " ".join([" ".join(self.data.documents[index]) for index in indices_documents])

        return context_selected, indices_documents