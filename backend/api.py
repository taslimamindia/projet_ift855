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
import time

# Fix Windows asyncio subprocess support: use Selector event loop on Windows
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


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
    data_folder: str = None

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

def create_default_model(settings: Settings):
    model = create_model(settings)
    response = model.aws_file.create_folder_in_aws(settings.default_folder, recreate=False)
    if response:
        model.data.documents = model.aws_file.download_file_from_aws("crawled_data", type_file="json")
        model.data.embeddings = model.aws_file.download_file_from_aws("embeddings", type_file="npy")
        model.data.chunks = model.aws_file.download_file_from_aws("crawled_chunks", type_file="json")
        model.data.sources = model.aws_file.download_file_from_aws("crawled_sources", type_file="json")
        model.faiss.create_faiss_index()
        model.data.documents_language = "french"
        model.data.query_language = "french"
    else:
        raise ValueError("Could not initialize default model; check AWS S3 settings and default folder.")
    return model

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize and clean up ML models on app startup/shutdown."""

    app.state.model = create_default_model(settings)
    app.state.models = {}
    
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
else:
    logger.info("CORS middleware not added for production environment.")


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

def get_aws_folder_path(data: dict | DataRequest, url: str) -> str:
    if (isinstance(data, DataRequest) and (data.data_folder == settings.default_folder)) or \
       (isinstance(data, dict) and (data.get("data_folder", None) == settings.default_folder)):
        aws_folder_path = settings.default_folder
    else:
        aws_folder_path = extract_aws_folder_path(url)
    return aws_folder_path

def get_clearml_step_command(step: str, url: str, folder: str, extra_args: list = None):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "clearml_pipeline.py")
    
    cmd_args = [sys.executable, script_path, "--step", step, "--url", url, "--folder", folder]
    if extra_args:
        cmd_args.extend(extra_args)
    return cmd_args

# --- Pipeline Manager for connection resilience ---
class PipelineManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.state: dict[str, dict] = {}
        self.history: dict[str, list[dict]] = {}
        self.in_progress: dict[str, bool] = {}
        self.last_activity: dict[str, float] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        # Cleanup old/stale clients before registering a new/returning one
        await self.cleanup_expired()
        # Endpoint must call websocket.accept() before
        self.active_connections[client_id] = websocket
        self.last_activity[client_id] = time.time()
        # Replay full history in order
        hist = self.history.get(client_id, [])
        for msg in hist:
            await self._send_to(client_id, msg)

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def _send_to(self, client_id: str, data: dict):
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_json(data)
            except (RuntimeError, WebSocketDisconnect, Exception):
                # Socket dead; attempt close and drop active link but keep history/state
                try:
                    await ws.close()
                except Exception:
                    pass
                self.disconnect(client_id)

    async def send_update(self, client_id: str, data: dict):
        # Persist last state and append to history
        self.state[client_id] = data
        self.history.setdefault(client_id, []).append(data)
        self.last_activity[client_id] = time.time()
        await self._send_to(client_id, data)

    def start_run(self, client_id: str):
        # Start a fresh history for a new pipeline run
        self.history[client_id] = []
        self.state.pop(client_id, None)
        self.in_progress[client_id] = True
        self.last_activity[client_id] = time.time()

    def finish_run(self, client_id: str):
        # Mark run finished and clear persisted history/state
        self.in_progress[client_id] = False
        self.history.pop(client_id, None)
        self.state.pop(client_id, None)
        self.last_activity[client_id] = time.time()

    def is_running(self, client_id: str) -> bool:
        return self.in_progress.get(client_id, False)

    async def cleanup_expired(self, max_age_seconds: int = 24 * 60 * 60):
        now = time.time()
        # Consider all known client_ids across maps
        all_ids = set(self.last_activity.keys()) | set(self.history.keys()) | set(self.state.keys()) | set(self.active_connections.keys()) | set(self.in_progress.keys())
        for cid in list(all_ids):
            last = self.last_activity.get(cid, 0)
            if now - last > max_age_seconds:
                ws = self.active_connections.pop(cid, None)
                if ws:
                    try:
                        await ws.close()
                    except Exception:
                        pass
                self.history.pop(cid, None)
                self.state.pop(cid, None)
                self.in_progress.pop(cid, None)
                self.last_activity.pop(cid, None)

pipeline_manager = PipelineManager()

async def _process_and_send_line(line, sender, step_name: str, channel: str) -> bool:
    """Process a raw line from a stream and send a structured message via WebSocket.

    Handles both bytes and str input, extracts progress percentage if present,
    and sends an appropriate JSON payload. Returns False if a RuntimeError occurs
    (e.g., WebSocket closed) so callers can break their read loop.
    """
    try:
        if isinstance(line, bytes):
            decoded_line = line.decode('utf-8').strip()
        else:
            decoded_line = str(line).strip()

        percentage = None
        if "PROGRESS:" in decoded_line:
            match = re.search(r"PROGRESS:\s*(\d+)%", decoded_line)
            if match:
                percentage = int(match.group(1))

        if percentage is not None:
            msg = {"step": step_name, "status": "in_progress", "value": percentage}
        else:
            msg = {"step": step_name, "status": "log", "channel": channel, "message": decoded_line}
        await sender(msg)
        return True
    except RuntimeError:
        return False

async def stream_subprocess_output(cmd_args, sender, step_name: str):
    """Start a subprocess and stream its stdout/stderr to the WebSocket.

    Uses asyncio.create_subprocess_exec on non-Windows platforms.
    On Windows, falls back to subprocess.Popen with asyncio.to_thread to avoid
    NotImplementedError from ProactorEventLoop subprocess transport.
    """

    if not sys.platform.startswith("win"):
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def read_stream(stream, channel):
            while True:
                line = await stream.readline()
                if line:
                    should_continue = await _process_and_send_line(line, sender, step_name, channel)
                    if not should_continue:
                        break
                else:
                    break

        await asyncio.gather(
            read_stream(process.stdout, "stdout"),
            read_stream(process.stderr, "stderr")
        )
        return await process.wait()

    # Windows fallback: use blocking Popen and read lines in a thread
    process = subprocess.Popen(
        cmd_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )

    async def read_fp(fp, channel):
        while True:
            line = await asyncio.to_thread(fp.readline)
            if line:
                should_continue = await _process_and_send_line(line, sender, step_name, channel)
                if not should_continue:
                    break
            else:
                break

    await asyncio.gather(
        read_fp(process.stdout, "stdout"),
        read_fp(process.stderr, "stderr")
    )
    return await asyncio.to_thread(process.wait)

async def websocket_initialization(sender, data: dict) -> bool:
    url = data.get("url", None)

    if not url:
        await sender({"step": "initializing", "status": "failed", "error": "URL is required"})
        return False    
    await sender({"step": "initializing", "status": "start"})

    aws_folder_path = get_aws_folder_path(data, url)

    cmd_args = get_clearml_step_command("initializing", url, aws_folder_path, None)
    returncode = await stream_subprocess_output(cmd_args, sender, "initializing")

    if returncode == 0:
        model = create_model(settings)
        model.aws_file.create_folder_in_aws(aws_folder_path, recreate=False)
        app.state.models[aws_folder_path] = model
        await sender({"step": "initializing", "status": "done"})
        return True
    else:
        await sender({"step": "initializing", "status": "failed", "error": f"Process exited with code {returncode}"})
        return False

async def websocket_crawling(sender, data: dict) -> bool:
    max_depth = int(data.get("max_depth", 250))

    url = data.get("url", None)
    if not url or not max_depth:
        await sender({"step": "crawling", "status": "failed", "error": "URL and max_depth are required"})
        return False
    await sender({"step": "crawling", "status": "start"})
    
    aws_folder_path = get_aws_folder_path(data, url)

    cmd_args = get_clearml_step_command("crawling", url, aws_folder_path, ["--max_depth", str(max_depth)])
    returncode = await stream_subprocess_output(cmd_args, sender, "crawling")

    if returncode == 0:
        model = app.state.models.get(aws_folder_path, None)
        if model:
            model.data.documents = model.aws_file.download_file_from_aws("crawled_data", type_file="json")
        await sender({"step": "crawling", "status": "done"})
        return True
    else:
        await sender({"step": "crawling", "status": "failed", "error": f"Process exited with code {returncode}"})
        return False

async def websocket_embedding(sender, data: dict) -> bool:
    url = data.get("url", None)
    if not url:
        await sender({"step": "embedding", "status": "failed", "error": "URL is required"})
        return False
    await sender({"step": "embedding", "status": "start"})

    aws_folder_path = get_aws_folder_path(data, url)

    cmd_args = get_clearml_step_command("embedding", url, aws_folder_path, None)
    returncode = await stream_subprocess_output(cmd_args, sender, "embedding")

    if returncode == 0:
        model = app.state.models.get(aws_folder_path, None)
        if model:
            model.data.chunks = model.aws_file.download_file_from_aws("crawled_chunks", type_file="json")
            model.data.sources = model.aws_file.download_file_from_aws("crawled_sources", type_file="json")
            model.data.embeddings = model.aws_file.download_file_from_aws("embeddings", type_file="npy")
        await sender({"step": "embedding", "status": "done"})
        return True
    else:
        await sender({"step": "embedding", "status": "failed", "error": f"Process exited with code {returncode}"})
        return False

async def websocket_indexing(sender, data: dict) -> bool:
    url = data.get("url", None)

    if not url:
        await sender({"step": "indexing", "status": "failed", "error": "URL is required"})
        return False
    await sender({"step": "indexing", "status": "start"})

    try:
        aws_folder_path = get_aws_folder_path(data, url)
        model = app.state.models.get(aws_folder_path, None)
        if model:
            model.data.embeddings = model.aws_file.download_file_from_aws("embeddings", type_file="npy")
            model.data.sources = model.aws_file.download_file_from_aws("crawled_sources", type_file="json")
            model.faiss.create_faiss_index()
        await sender({"step": "indexing", "status": "done"})
        return True
    except Exception as e:
        await sender({"step": "indexing", "status": "failed", "error": str(e)})
        return False


@app.get("/")
def root():
    return {"message": "API is running. Visit /docs for API documentation."}

@app.get("/admin/api/config")
def admin_get_config():
    """Retrieve the current application configuration settings.

    Returns:
        dict: A dictionary containing key configuration parameters.
    """
    config = {
        "default_folder": settings.default_folder,
    }
    return config

@app.websocket("/admin/ws/memory")
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
        logger.info("Memory monitor WebSocket disconnected.")
    except Exception as e:
        logger.error(f"Error in memory monitor: {e}")
        try:
            await websocket.close()
        except RuntimeError:
            pass

@app.websocket("/api/pipeline")
async def guest_websocket_pipeline(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_json()
    # Force guest mode: no explicit data_folder (use default/extracted)
    data["data_folder"] = None
    # connection management
    client_id = data.get("client_id") or (data.get("url") or "guest")
    await pipeline_manager.connect(ws, client_id)

    async def sender(msg: dict):
        await pipeline_manager.send_update(client_id, msg)

    # If a run is already in progress, just stream history/live updates
    if not pipeline_manager.is_running(client_id):
        pipeline_manager.start_run(client_id)

        any_failed = False
        ok_init = await websocket_initialization(sender, data)
        if not ok_init:
            any_failed = True
        else:
            ok_crawl = await websocket_crawling(sender, data)
            if not ok_crawl:
                any_failed = True
            else:
                ok_embed = await websocket_embedding(sender, data)
                if not ok_embed:
                    any_failed = True
                else:
                    ok_index = await websocket_indexing(sender, data)
                    if not ok_index:
                        any_failed = True

        if any_failed:
            await sender({"step": "pipeline", "status": "failed", "error": "One or more steps failed"})
        else:
            await sender({"step": "pipeline", "status": "done"})
        pipeline_manager.finish_run(client_id)
    else:
        # Wait until current run finishes to keep WS open for live updates
        try:
            while pipeline_manager.is_running(client_id):
                await asyncio.sleep(0.5)
        except WebSocketDisconnect:
            pass

    pipeline_manager.disconnect(client_id)
    try:
        await ws.close()
    except Exception:
        pass

@app.websocket("/admin/api/pipeline")
async def admin_websocket_pipeline(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_json()

    # Admin: respect provided data_folder, defaulting to settings.default_folder if missing
    client_id = data.get("client_id") or (data.get("url") or "admin")
    await pipeline_manager.connect(ws, client_id)

    async def sender(msg: dict):
        await pipeline_manager.send_update(client_id, msg)

    if not pipeline_manager.is_running(client_id):
        pipeline_manager.start_run(client_id)

        any_failed = False
        ok_init = await websocket_initialization(sender, data)
        if not ok_init:
            any_failed = True
        else:
            ok_crawl = await websocket_crawling(sender, data)
            if not ok_crawl:
                any_failed = True
            else:
                ok_embed = await websocket_embedding(sender, data)
                if not ok_embed:
                    any_failed = True
                else:
                    ok_index = await websocket_indexing(sender, data)
                    if not ok_index:
                        any_failed = True

        if any_failed:
            await sender({"step": "pipeline", "status": "failed", "error": "One or more steps failed"})
        else:
            if data.get("data_folder", None) == settings.default_folder:
                app.state.model = create_default_model(settings)
            await sender({"step": "pipeline", "status": "done"})
        pipeline_manager.finish_run(client_id)
    else:
        try:
            while pipeline_manager.is_running(client_id):
                await asyncio.sleep(0.5)
        except WebSocketDisconnect:
            pass

    pipeline_manager.disconnect(client_id)
    try:
        await ws.close()
    except Exception:
        pass

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
            datarequest.data_folder = None
            aws_folder_path = get_aws_folder_path(datarequest, datarequest.url)
            model = app.state.models.get(aws_folder_path, None)
            if model is None:
                raise ValueError(f"No model found for domain extracted from URL: {datarequest.url}")

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

@dataclass
class DeleteModelRequest:
    """Request payload for deleting a domain-specific model.

    Attributes:
        url (str): The URL used to identify the domain-specific model to delete.
    """
    folders: list[str]
    
@app.post("/admin/api/folders/delete")
def delete_folders(folders: list[str]):
    """Delete specified folders from AWS S3 and unload related models from memory."""
    print("diallo", folders)
    try:
        model = app.state.model
        if not isinstance(folders, list) or len(folders) == 0:
            return "No folders specified for deletion."
        if model.aws_file.delete_folders_in_aws(settings.base_prefix, folders):
            return "Folders deleted successfully."
        else:
            return "Folder deletion failed."
    except Exception as e:
        raise e

@app.get("/admin/api/folders/list")
def list_folders():
    """List all folders in the AWS S3 bucket used for storing domain data."""
    model = app.state.model
    folders = model.aws_file.list_folders_in_aws(settings.base_prefix)
    folders = [folder for folder in folders if folder != settings.default_folder]
    return folders