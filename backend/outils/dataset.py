from dataclasses import dataclass
from typing import Any
import numpy as np
import faiss


@dataclass
class Data:
    """Container class to store data used throughout the application.

    This class centralizes all the core data structures required for
    document processing, embedding generation, and vector database indexing.
    It is designed to be passed between different components of the
    application for further processing.

    Attributes:
        documents (dict): 
            A dictionary where each key is a URL (str) and each value is a list of strings
            representing the textual content associated with that URL.
        
        chunks (list): 
            A flattened list of all text segments extracted from `documents`,
            prepared for vectorization.
        
        sources (list): 
            A flattened list of URLs corresponding to each text segment in `chunks`.
            Ensures traceability between chunks and their original source.
        
        embeddings (numpy.ndarray): 
            A matrix of embeddings generated from `chunks`, used for similarity search
            and vector database queries.
        
        index (faiss.swigfaiss_avx2.IndexFlatL2): 
            The FAISS index structure used to store and query embeddings efficiently.
        
        fireworks_api_key (str): 
            API key for Fireworks model access.
    """

    documents: dict = None
    chunks: list = None
    sources: list = None
    embeddings: np.ndarray = None
    index: Any = None
    fireworks_api_key: str = None
    documents_language: str = None
    query_language: str = None