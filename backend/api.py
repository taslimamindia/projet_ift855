import re
import sys
import asyncio
import subprocess
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dataclasses import dataclass
from contextlib import asynccontextmanager
import tldextract
import logging
from config import *
from outils.dataset import Data
from outils.filesmanager import FileManager, AWSFileManager
from outils.webcrawling import Crawling
from models.embeddings import Embeddings
from models.faissmanager import Faiss
from models.LLM import Fireworks_LLM
from models.RAG import LangChainRAGAgent
from load_settings import settings
import psutil


_uvicorn_logger = logging.getLogger("uvicorn.error")
logger = _uvicorn_logger if _uvicorn_logger.handlers else logging.getLogger(__name__)


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


def run_clearml_step(step: str, url: str, extra_args: list = None):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "clearml_pipeline.py")
    
    cmd_args = ["--step", step, "--url", url]
    if extra_args:
        cmd_args.extend(extra_args)
        
    return subprocess.run(
        [sys.executable, script_path] + cmd_args,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )


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

    logger.info("Starting up: Initializing default model...")
    logger.info("Environment variables: " + str(settings))

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
    logger.info("Default model initialized and ready.")
    
    yield
    
    model = None


app = FastAPI(lifespan=lifespan)


if settings.env.lower() == "env":
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware added for development environment.")
elif settings.env.lower() == "gcloudprod":
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://mlops.kassatech.org",
            "https://kassatech.org"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware added for gcloudprod environment.")
else:
    logger.info("Production environment detected; CORS middleware not added, it will be managed by nginx proxy.")


@app.get("/")
def root():
    return {"message": "API is running. Visit /docs for API documentation."}


@app.websocket("/ws/memory")
async def memory_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            process = psutil.Process()
            mem_info = process.memory_info()
            virtual_mem = psutil.virtual_memory()

            data = {
                "rss_GB": round(mem_info.rss / (1024 ** 3), 3),   # Physical memory of the process
                "vms_GB": round(mem_info.vms / (1024 ** 3), 3),   # Virtual memory of the process
                "cpu_percent": process.cpu_percent(interval=None), # CPU usage of the process (%)
                "threads": process.num_threads(),                 # Number of threads
                "total_RAM_GB": round(virtual_mem.total / (1024 ** 3), 2), # Total machine RAM
                "used_RAM_GB": round(virtual_mem.used / (1024 ** 3), 2),   # Used machine RAM
                "ram_percent": virtual_mem.percent                # Total RAM usage (%)
            }

            await websocket.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Client disconnected from memory monitor")
    except Exception as e:
        print(f"Error in memory monitor: {e}")
        try:
            await websocket.close()
        except RuntimeError:
            pass


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

    # Run ClearML task in subprocess using run_in_executor to avoid Windows loop issues
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, run_clearml_step, "initializing", url, None)

    if result.returncode == 0:
        aws_folder_path = extract_aws_folder_path(url)
        model = create_model(settings)
        model.aws_file.create_folder_in_aws(aws_folder_path, recreate=False)
        app.state.models[aws_folder_path] = model
        await ws.send_json({"step": "initializing", "status": "done"})
    else:
        logger.error(f"Initializing failed: {result.stderr}")
        await ws.send_json({"step": "initializing", "status": "failed", "error": result.stderr})
    await ws.close()


@app.websocket("/api/pipeline/crawling")
async def websocket_crawling(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_json()
    max_depth = int(data.get("max_depth", 250))

    url = data.get("url", None)
    if not url or not max_depth:
        await ws.send_json({"step": "crawling", "status": "failed", "error": "URL and max_depth are required"})
        await ws.close()
        return
    
    # Run ClearML task in subprocess
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, run_clearml_step, "crawling", url, ["--max_depth", str(max_depth)])

    if result.returncode == 0:
        aws_folder_path = extract_aws_folder_path(url)
        model = app.state.models.get(aws_folder_path, None)
        if model:
            # Reload data from S3
            model.data.documents = model.aws_file.download_file_from_aws("crawled_data", type_file="json")
        await ws.send_json({"step": "crawling", "status": "done"})
    else:
        logger.error(f"Crawling failed: {result.stderr}")
        await ws.send_json({"step": "crawling", "status": "failed", "error": result.stderr})
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

    # Run ClearML task in subprocess
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, run_clearml_step, "embedding", url, None)

    if result.returncode == 0:
        aws_folder_path = extract_aws_folder_path(url)
        model = app.state.models.get(aws_folder_path, None)
        if model:
            # Reload data from S3
            model.data.chunks = model.aws_file.download_file_from_aws("crawled_chunks", type_file="json")
            model.data.sources = model.aws_file.download_file_from_aws("crawled_sources", type_file="json")
            model.data.embeddings = model.aws_file.download_file_from_aws("embeddings", type_file="npy")
        await ws.send_json({"step": "embedding", "status": "done"})
    else:
        logger.error(f"Embedding failed: {result.stderr}")
        await ws.send_json({"step": "embedding", "status": "failed", "error": result.stderr})
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

    # Run ClearML task in subprocess
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, run_clearml_step, "indexing", url, None)

    if result.returncode == 0:
        aws_folder_path = extract_aws_folder_path(url)
        model = app.state.models.get(aws_folder_path, None)
        if model:
            # Recreate index locally
            model.faiss.create_faiss_index()
        await ws.send_json({"step": "indexing", "status": "done"})
    else:
        logger.error(f"Indexing failed: {result.stderr}")
        await ws.send_json({"step": "indexing", "status": "failed", "error": result.stderr})
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