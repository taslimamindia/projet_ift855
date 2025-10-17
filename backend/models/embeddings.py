from langchain.text_splitter import RecursiveCharacterTextSplitter
from fireworks.client import Fireworks
from outils.dataset import Data
import numpy as np


class Embeddings:
    def __init__(self, data:Data, model_embedding_name="nomic-ai/nomic-embed-text-v1.5"):
        self.data = data
        self.model_embedding_name=model_embedding_name


    def flat_chunks_and_sources(self):
        """
        Flatten nested lists of chunks and sources stored in `self.data`.

        This method iterates over paired elements from `self.data.sources` and `self.data.chunks`,
        concatenates all nested lists into single flat lists, and updates `self.data.chunks` 
        and `self.data.sources` with these flattened versions.

        Example:
            Suppose:
                self.data.chunks = [["a1", "a2"], ["b1", "b2"]]
                self.data.sources = [["srcA", "srcA"], ["srcB", "srcB"]]

            After calling this method:
                self.data.chunks = ["a1", "a2", "b1", "b2"]
                self.data.sources = ["srcA", "srcA", "srcB", "srcB"]
        """
        chunks = []
        sources = []

        for source, chunk in zip(self.data.sources, self.data.chunks):
            chunks += chunk
            sources += source
        
        self.data.chunks = chunks
        self.data.sources = sources

    
    def chunking(self, chunk_size=500, overlap=50):
        """
        Split documents into overlapping text chunks for processing or embedding.

        This method uses a `RecursiveCharacterTextSplitter` to divide each document’s text 
        into smaller segments (`chunks`) of a specified size, allowing for overlapping 
        regions to preserve context between adjacent chunks. It stores both the resulting 
        chunks and their associated source URLs.

        Args:
            chunk_size (int, optional): Maximum number of characters per chunk. Defaults to 500.
            overlap (int, optional): Number of overlapping characters between consecutive chunks. Defaults to 50.

        Side Effects:
            - Populates `self.data.chunks` with lists of text chunks for each document.
            - Populates `self.data.sources` with lists of source URLs corresponding to each chunk.

        Example:
            Suppose:
                self.data.documents = {
                    "https://example.com": "Long document text..."
                }

            After calling:
                self.data.chunks = [["chunk_1", "chunk_2", ...]]
                self.data.sources = [["https://example.com", "https://example.com", ...]]
        """

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

        self.data.chunks = []
        self.data.sources = []
        for url, passages in self.data.documents.items():
            chunk = splitter.split_text(passages)
            self.data.chunks.append(chunk)
            self.data.sources.append([url] * len(chunk))
    

    def fireworks_embeddings(self):
        """Generate embeddings for the chunks stored in self.data.chunks using Fireworks API.

        Args:
            query (str): The input text to be embedded.
        """
        
        self.data.embeddings = []

        def split_list(lst, n):
            k, m = divmod(len(lst), n)
            return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]
        chunks = split_list(self.data.chunks, 50)

        with Fireworks(api_key=self.data.fireworks_api_key) as fw:
            for chunk in chunks:
                response = fw.embeddings.create(
                    model=self.model_embedding_name,
                    input=chunk
                )
                self.data.embeddings += [np.array(item.embedding) for item in response.data]
        self.data.embeddings = np.array(self.data.embeddings)
    

    def fireworks_encoding_query(self, query):
        """Generate embeddings for the chunks stored in self.data.chunks using Fireworks API.

        Args:
            query (str): The input text to be embedded.
            
        Returns:
            (numpy.ndarray): result of embeddings.
        """

        with Fireworks(api_key=self.data.fireworks_api_key) as fw:
            response = fw.embeddings.create(
                model=self.model_embedding_name,
                input=query
            )
            return response.data[0].embedding