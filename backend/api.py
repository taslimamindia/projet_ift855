# from typing import Union
import re
from fastapi import FastAPI, WebSocket
from dataclasses import dataclass
from contextlib import asynccontextmanager
import tldextract

from config import *
from outils.dataset import Data
from outils.filesmanager import FileManager, AWSFileManager
from outils.webcrawling import Crawling
from models.embeddings import Embeddings
from models.faissmanager import Faiss
from models.LLM import Fireworks_LLM
from models.RAG import LangChainRAGAgent
from load_settings import settings


@dataclass
class Model:
    """
    Core application model that aggregates all major components.

    Attributes:
        data (Data): Central data container for documents, embeddings, and index structures.
        crawling (Crawling): Module responsible for web scraping and content extraction.
        embeddings (Embeddings): Handles embedding generation and related operations.
        file (FileManager): Manages file storage, loading, and persistence.
        faiss (Faiss): Handles FAISS index creation, querying, and updates.
        llm (Fireworks_LLM): Interface to the Fireworks language model for text generation and QA tasks.
    """

    data: Data = None
    crawling: Crawling = None
    embeddings: Embeddings = None
    file: FileManager = None
    faiss: Faiss = None
    llm: Fireworks_LLM = None
    rag_langchain: LangChainRAGAgent = None
    aws_file: AWSFileManager = None


def create_model(settings: Settings):
    model = Model()

    model.data = Data(fireworks_api_key=settings.fireworks_api_key)
    model.crawling = Crawling()
    model.embeddings = Embeddings(model.data, settings.model_embeddings_name)
    model.file = FileManager(model.data)
    model.faiss = Faiss(model.data, model.embeddings)
    model.llm = Fireworks_LLM(model.data, settings.model_llm_name, settings.deployment_type)
    model.rag_langchain = LangChainRAGAgent(model.data, model.faiss, model.llm)
    model.aws_file = AWSFileManager(
        data=model.data,
        base_prefix=settings.base_prefix,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        aws_region=settings.aws_region,
        aws_s3_bucket_name=settings.aws_s3_bucket_name_backend
    )

    return model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize and clean up ML models on app startup/shutdown."""

    model = create_model(settings)
    model.data.documents = model.aws_file.download_file_from_aws("crawled_data", type_file="json")
    model.data.embeddings = model.aws_file.download_file_from_aws("embeddings", type_file="npy")
    model.data.chunks = model.aws_file.download_file_from_aws("crawled_chunks", type_file="json")
    model.data.sources = model.aws_file.download_file_from_aws("crawled_sources", type_file="json")
    model.faiss.create_faiss_index()
    model.data.documents_language = "french"
    model.data.query_language = "french"

    app.state.model = model
    app.state.models = {}
    
    yield
    
    model = None


app = FastAPI(lifespan=lifespan)


if settings.env.lower() == "env":
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def root():
    return {"message": "API is running. Visit /docs for API documentation."}


@dataclass
class DataRequest:
    """Request payload for RAG/chat endpoints.

    Attributes:
        query (str): The user question or query text.
        url (str): Optional URL used to select a domain-specific model.
        mode (str): Optional mode flag.
        k (int): Number of retrieved documents to use (default: 5).
    """

    query: str = None
    url: str = None
    mode: str = None
    k: int = 5
    max_depth: int = 200


def extract_domain(url: str) -> str:
    """Extract the domain from a given URL.

    Args:
        url (str): The input URL.

    Returns:
        str: The extracted domain.
    """
    ext = tldextract.extract(url)
    return f"{ext.domain}_{ext.suffix}"


def extract_aws_folder_path(url: str) -> str:
    """Extract the AWS folder path from a given URL.

    Args:
        url (str): The input URL.

    Returns:
        str: The extracted AWS folder path.
    """
    
    name = re.sub(r'[^A-Za-z0-9]+', '_', url)
    name = name.replace("_", "")

    if not name:
        raise ValueError("Could not extract domain from URL.")
    
    return name.lower()



@app.websocket("/api/pipeline/initializing")
async def websocket_initialization(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_json()
    url = data.get("url", None)

    if not url:
        await ws.send_json({"step": "initializing", "status": "failed", "error": "URL is required"})
        await ws.close()
        return

    domain = extract_domain(url)
    aws_folder_path = extract_aws_folder_path(url)
    model = create_model(settings)
    app.state.models[aws_folder_path] = model
    if model.aws_file.create_folder_in_aws(aws_folder_path, True):
        meta_data = {"domain": domain, "url": url, "aws_folder_path": aws_folder_path}
        if model.aws_file.upload_file_in_aws("metadata", meta_data, type_file="json") is not True:
            await ws.send_json({"step": "initializing", "status": "failed", "error": "Failed to upload metadata to AWS"})
            await ws.close()
            return
        await ws.send_json({"step": "initializing", "status": "done"})
    else:
        await ws.send_json({"step": "initializing", "status": "failed", "error": "Failed to create folder in AWS"})
    await ws.close()


@app.websocket("/api/pipeline/crawling")
async def websocket_crawling(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_json()
    max_depth = int(data.get("max_depth", 250))
    print(f"Max depth received: {max_depth}")
    url = data.get("url", None)

    if not url or not max_depth:
        await ws.send_json({"step": "crawling", "status": "failed", "error": "URL and max_depth are required"})
        await ws.close()
        return
    else:
        aws_folder_path = extract_aws_folder_path(url)
        model = app.state.models.get(aws_folder_path, None)

        if model is None:
            await ws.send_json({"step": "crawling", "status": "failed", "error": "Model not initialized for this domain"})
            await ws.close()
            return
        model.crawling.crawl(url, max_depth=max_depth)
        model.data.documents = model.crawling.texts
        if model.aws_file.upload_file_in_aws("crawled_data", model.data.documents, type_file="json") is True:
            await ws.send_json({"step": "crawling", "status": "done"})
        else:
            await ws.send_json({"step": "crawling", "status": "failed", "error": "Failed to upload crawled data to AWS"})
        await ws.close()


@app.websocket("/api/pipeline/embedding")
async def websocket_embedding(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_json()
    url = data.get("url", None)
    if not url:
        await ws.send_json({"step": "embedding", "status": "failed", "error": "URL is required"})
        await ws.close()
        return

    # proceed with embedding when URL is provided
    else:
        model = app.state.models.get(extract_aws_folder_path(url), None)
        
        if model is None:
            await ws.send_json({"step": "embedding", "status": "failed", "error": "Model not initialized for this domain"})
            await ws.close()
            return
        
        model.embeddings.chunking()
        if model.aws_file.upload_file_in_aws("crawled_chunks", model.data.chunks, type_file="json") is not True:
            await ws.send_json({"step": "embedding", "status": "failed", "error": "Failed to upload chunks to AWS"})
            await ws.close()
            return
            
        # await asyncio.to_thread(model.embeddings.flat_chunks_and_sources)
        model.embeddings.flat_chunks_and_sources()
        if model.aws_file.upload_file_in_aws("crawled_sources", model.data.sources, type_file="json") is not True:
            await ws.send_json({"step": "embedding", "status": "failed", "error": "Failed to upload sources to AWS"})
            await ws.close()
            return

        # await asyncio.to_thread(model.embeddings.fireworks_embeddings)
        model.embeddings.fireworks_embeddings()
        if model.aws_file.upload_file_in_aws("embeddings", model.data.embeddings, type_file="npy") is not True:
            await ws.send_json({"step": "embedding", "status": "failed", "error": "Failed to upload embeddings to AWS"})
            await ws.close()
            return

        await ws.send_json({"step": "embedding", "status": "done"})
        await ws.close()


@app.websocket("/api/pipeline/indexing")
async def websocket_indexing(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_json()

    url = data.get("url", None)
    if not url:
        await ws.send_json({"step": "indexing", "status": "failed", "error": "URL is required"})
        await ws.close()
        return
    else:
        model = app.state.models.get(extract_aws_folder_path(url), None)
        model.faiss.create_faiss_index()
        await ws.send_json({"step": "indexing", "status": "done"})
        await ws.close()


@app.post("/api/chat/rag")
async def chat_rag(datarequest: DataRequest):
    """Answer a query using the LangChain-based RAG agent.

    The function selects either the global default model or a domain-specific model
    (based on the provided `url`) and returns the generated answer string.

    Args:
        datarequest (DataRequest): The request payload containing the query, optional URL, mode and k.
    
    Returns:
        dict: A dictionary containing the original query and the generated response.
    """

    try:
        k = datarequest.k or 5

        if not datarequest.url:
            model = app.state.model
        else:
            aws_folder_path = extract_aws_folder_path(datarequest.url)
            model = app.state.models.get(aws_folder_path, None)
            if model is None:
                raise ValueError(f"No model found for domain: {aws_folder_path}")

        if model is None or model.data is None:
            raise ValueError("No default model found or initialized.")
        else:
            model.data.documents_language = model.llm.detect_language_of_documents(model.data.documents)
            if datarequest.query and datarequest.query.strip():
                model.data.query_language = model.llm.detect_language(datarequest.query)

        result = model.rag_langchain.answer(datarequest.query, k=k)
        return {"query": datarequest.query, "response": result.get("response")}
    
    except Exception as e:
        raise e