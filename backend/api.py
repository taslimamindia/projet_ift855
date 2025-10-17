# from typing import Union
from fastapi import FastAPI, WebSocket
from dataclasses import dataclass
from contextlib import asynccontextmanager
import tldextract

from config import *
from outils.dataset import Data
from outils.filesmanager import FileManager
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


def create_model(settings: Settings):
    model = Model()

    model.data = Data(fireworks_api_key=settings.fireworks_api_key)
    model.crawling = Crawling()
    model.embeddings = Embeddings(model.data, settings.model_embeddings_name)
    model.file = FileManager(model.data)
    model.faiss = Faiss(model.data, model.embeddings)
    model.llm = Fireworks_LLM(model.data, settings.model_llm_name, settings.deployment_type)

    model.rag_langchain = LangChainRAGAgent(model.data, model.faiss, model.llm)

    return model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    model = create_model(settings)
    model.data.documents = model.file.load_texts_from_json("./datasets/crawled_data.json")
    model.file.load_embeddings("./datasets/")
    model.data.chunks = model.file.load_texts_from_json("./datasets/crawled_chunks.json")
    model.data.sources = model.file.load_texts_from_json("./datasets/crawled_sources.json")
    model.faiss.create_faiss_index()

    app.state.model = model
    app.state.models = {}

    
    yield
    
    # Clean up the ML models and release the resources
    model = None


app = FastAPI(lifespan=lifespan)


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


def extract_domain(url: str) -> str:
    """Extract the domain from a given URL.

    Args:
        url (str): The input URL.

    Returns:
        str: The extracted domain.
    """
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}"


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
    model = create_model(settings)
    app.state.models[domain] = model
    await ws.send_json({"step": "initializing", "status": "done"})
    await ws.close()


@app.websocket("/api/pipeline/crawling")
async def websocket_crawling(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_json()

    url = data.get("url", None)
    if not url:
        await ws.send_json({"step": "crawling", "status": "failed", "error": "URL is required"})
        await ws.close()
        return

    # proceed with crawling when URL is provided
    else:
        max_depth = data.get("k", 3)
        model = app.state.models.get(extract_domain(url), None)
        if model is None:
            await ws.send_json({"step": "crawling", "status": "failed", "error": "Model not initialized for this domain"})
            await ws.close()
            return
        model.crawling.crawl_with_control(url, max_depth=max_depth)
        model.data.documents = model.crawling.texts
        await ws.send_json({"step": "crawling", "status": "done"})
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
        model = app.state.models.get(extract_domain(url), None)
        
        if model is None:
            await ws.send_json({"step": "embedding", "status": "failed", "error": "Model not initialized for this domain"})
            await ws.close()
            return
        
        model.embeddings.chunking()
        # await asyncio.to_thread(model.embeddings.flat_chunks_and_sources)
        model.embeddings.flat_chunks_and_sources()
        # await asyncio.to_thread(model.embeddings.fireworks_embeddings)
        model.embeddings.fireworks_embeddings()
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

    # proceed with indexing when URL is provided
    else:
        model = app.state.models.get(extract_domain(url), None)
        model.faiss.create_faiss_index()
        await ws.send_json({"step": "indexing", "status": "done"})
        await ws.close()

# @app.websocket("/api/pipeline/initialize")
# async def websocket_pipeline(ws: WebSocket):
#     await ws.accept()

#     try:
#         data = await ws.receive_json()
#         url = data.get("url", None)
#         print(url, "initialize")

#         if not url:
#             # print("URL manquante")
#             await ws.send_json({"step": "pipeline", "status": "failed", "error": "URL manquante"})
#             await ws.close()
#             return

#         model, domain = await initialization(url)
        
#         print(f"Starting pipeline for URL: {url} under domain: {domain}")
#         print("crawling...")
#         # --- 1. CRAWLING ---
#         await ws.send_json({"step": "crawling", "status": "start"})
#         await process_crawling(model=model, url=url, max_depth=3)
#         await ws.send_json({"step": "crawling", "status": "done"})

#         print("embedding...")
#         # --- 2. EMBEDDINGS ---
#         await ws.send_json({"step": "embedding", "status": "start"})
#         await process_embedding(model=model)
#         await ws.send_json({"step": "embedding", "status": "done"})

#         print("indexing...")
#         # --- 3. INDEXING ---
#         await ws.send_json({"step": "indexing", "status": "start"})
#         await process_indexing(model=model)
#         await ws.send_json({"step": "indexing", "status": "done"})

#         print("End...")
#         # --- End of the PIPELINE ---
#         await ws.send_json({"step": "pipeline", "status": "done"})
#         await ws.close()

    # except Exception as e:
    #     await ws.send_json({"error": str(e)})
    #     await ws.close()


@app.post("/api/chat/rag")
async def chat_rag(datarequest: DataRequest):
    """Answer a query using the LangChain-based RAG agent.

    The function selects either the global default model or a domain-specific model
    (based on the provided `url`) and returns the generated answer string.
    """

    k = datarequest.k or 5
    if not datarequest.url:
        model = app.state.model
    else:
        domain = extract_domain(datarequest.url)
        model = app.state.models.get(domain, None)
        if model is None:
            raise ValueError(f"No model found for domain: {domain}")

    result = model.rag_langchain.answer(datarequest.query, k=k)
    return {"query": datarequest.query, "response": result.get("response")}


@app.get("/config")
def get_config():
    return {
        "env": settings.env,
        "embedding_model": settings.model_embeddings_name,
        "llm_model": settings.model_llm_name,
        "deployment": settings.deployment_type,
    }
