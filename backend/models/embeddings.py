from langchain.text_splitter import RecursiveCharacterTextSplitter
from fireworks.client import Fireworks
from outils.dataset import Data
import numpy as np
from tqdm import tqdm
import logging


# Prefer uvicorn's logger when running under uvicorn; fall back to module logger
_uvicorn_logger = logging.getLogger("uvicorn.error")
logger = _uvicorn_logger if _uvicorn_logger.handlers else logging.getLogger(__name__)


class Embeddings:
    def __init__(self, data:Data, model_embedding_name="nomic-ai/nomic-embed-text-v1.5"):
        self.data = data
        self.model_embedding_name=model_embedding_name


    def flat_chunks_and_sources(self):
        """
        Flatten nested lists of chunks and sources stored in `self.data`.
        Also filters out empty or whitespace-only chunks.
        """
        chunks = []
        sources = []

        for source_list, chunk_list in zip(self.data.sources, self.data.chunks):
            for src, txt in zip(source_list, chunk_list):
                if txt and txt.strip():
                    chunks.append(txt)
                    sources.append(src)
        
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
    

    def fireworks_embeddings(self, dividend=50):
        """Generate embeddings for the chunks stored in self.data.chunks using Fireworks API.

        Args:
            query (str): The input text to be embedded.
        """
        
        self.data.embeddings = []
        n = len(self.data.chunks)
        if n == 0:
            logger.warning("No chunks to embed.")
            self.data.embeddings = np.array([])
            return

        q = n // dividend
        r = n % dividend

        chunks = [self.data.chunks[i * dividend: (i + 1) * dividend] for i in range(q)]
        if r > 0:
            chunks.append(self.data.chunks[q * dividend: q * dividend + r])
        logger.debug(f"chunks sizes: {[len(c) for c in chunks]}")

        with Fireworks(api_key=self.data.fireworks_api_key) as fw:
            total_chunks = len(chunks)
            for i, chunk in enumerate(tqdm(chunks, desc="Generating embeddings", colour="green")):
                # Log progress for frontend tracking
                progress_percent = int(((i + 1) / total_chunks) * 100)
                logger.info(f"PROGRESS: {progress_percent}% - Embedding batch {i+1}/{total_chunks}")
                
                try:
                    response = fw.embeddings.create(
                        model=self.model_embedding_name,
                        input=chunk
                    )
                    self.data.embeddings += [np.array(item.embedding) for item in response.data]
                except Exception as e:
                    logger.error(f"Error embedding chunk batch: {e}")
                    # Optionally retry or skip? For now, we raise to stop the pipeline if critical
                    raise e
        self.data.embeddings = np.array(self.data.embeddings)
    

    def fireworks_encoding_query(self, query):
        """Generate embeddings for the chunks stored in self.data.chunks using Fireworks API.

        Args:
            query (str): The input text to be embedded.
            
        Returns:
            (numpy.ndarray): result of embeddings.
        """
        if not query or not query.strip():
            logger.warning("Empty query provided for embedding.")
            # Return a zero vector or handle appropriately. 
            # For now, let's assume we shouldn't be here with empty query.
            # But to avoid API error:
            return np.zeros(768) # Assuming 768 dim, but better to raise or handle upstream

        with Fireworks(api_key=self.data.fireworks_api_key) as fw:
            try:
                response = fw.embeddings.create(
                    model=self.model_embedding_name,
                    input=query
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Error embedding query '{query}': {e}")
                raise e