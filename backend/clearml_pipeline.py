import argparse
import sys
import os
import logging

# Add the current directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clearml import Task
from load_settings import settings
from api import create_model, extract_aws_folder_path, extract_domain

# Configure ClearML environment if settings are present
if settings.clearml_web_host:
    os.environ["CLEARML_WEB_HOST"] = settings.clearml_web_host
if settings.clearml_api_host:
    os.environ["CLEARML_API_HOST"] = settings.clearml_api_host
if settings.clearml_files_host:
    os.environ["CLEARML_FILES_HOST"] = settings.clearml_files_host
if settings.clearml_api_access_key:
    os.environ["CLEARML_API_ACCESS_KEY"] = settings.clearml_api_access_key
if settings.clearml_api_secret_key:
    os.environ["CLEARML_API_SECRET_KEY"] = settings.clearml_api_secret_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_initializing(url):
    task = Task.init(project_name="RAG_Pipeline", task_name="initializing", reuse_last_task_id=False)
    task.connect({"url": url})
    
    try:
        aws_folder_path = extract_aws_folder_path(url)
        domain = extract_domain(url)
        
        model = create_model(settings)
        
        if model.aws_file.create_folder_in_aws(aws_folder_path, True):
            meta_data = {"domain": domain, "url": url, "aws_folder_path": aws_folder_path}
            model.aws_file.upload_file_in_aws("metadata", meta_data, type_file="json")
            logger.info("Initializing done")
        else:
            logger.error("Initializing failed")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Error in initializing: {e}")
        sys.exit(1)
    finally:
        task.close()

def run_crawling(url, max_depth):
    task = Task.init(project_name="RAG_Pipeline", task_name="crawling", reuse_last_task_id=False)
    task.connect({"url": url, "max_depth": max_depth})
    
    try:
        aws_folder_path = extract_aws_folder_path(url)
        model = create_model(settings)
        # Navigate to the folder
        model.aws_file.create_folder_in_aws(aws_folder_path, recreate=False)
        
        model.crawling.crawl(url, max_depth=max_depth)
        model.data.documents = model.crawling.texts
        
        if model.aws_file.upload_file_in_aws("crawled_data", model.data.documents, type_file="json"):
            logger.info("Crawling done")
        else:
            logger.error("Crawling failed")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Error in crawling: {e}")
        sys.exit(1)
    finally:
        task.close()

def run_embedding(url):
    task = Task.init(project_name="RAG_Pipeline", task_name="embedding", reuse_last_task_id=False)
    task.connect({"url": url})
    
    try:
        aws_folder_path = extract_aws_folder_path(url)
        model = create_model(settings)
        model.aws_file.create_folder_in_aws(aws_folder_path, recreate=False)
        
        # Download crawled data
        logger.info("Downloading crawled data...")
        model.data.documents = model.aws_file.download_file_from_aws("crawled_data", type_file="json")
        
        logger.info("Chunking...")
        model.embeddings.chunking()
        model.aws_file.upload_file_in_aws("crawled_chunks", model.data.chunks, type_file="json")
        
        logger.info("Processing sources...")
        model.embeddings.flat_chunks_and_sources()
        model.aws_file.upload_file_in_aws("crawled_sources", model.data.sources, type_file="json")
        
        logger.info("Generating embeddings...")
        model.embeddings.fireworks_embeddings()
        model.aws_file.upload_file_in_aws("embeddings", model.data.embeddings, type_file="npy")
        
        logger.info("Embedding done")
    except Exception as e:
        logger.exception(f"Error in embedding: {e}")
        sys.exit(1)
    finally:
        task.close()

def run_indexing(url):
    task = Task.init(project_name="RAG_Pipeline", task_name="indexing", reuse_last_task_id=False)
    task.connect({"url": url})
    
    try:
        aws_folder_path = extract_aws_folder_path(url)
        model = create_model(settings)
        model.aws_file.create_folder_in_aws(aws_folder_path, recreate=False)
        
        logger.info("Downloading embeddings and sources...")
        model.data.embeddings = model.aws_file.download_file_from_aws("embeddings", type_file="npy")
        model.data.sources = model.aws_file.download_file_from_aws("crawled_sources", type_file="json")
        
        logger.info("Creating FAISS index...")
        model.faiss.create_faiss_index()
        
        logger.info("Indexing done")
    except Exception as e:
        logger.exception(f"Error in indexing: {e}")
        sys.exit(1)
    finally:
        task.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", required=True, choices=["initializing", "crawling", "embedding", "indexing"])
    parser.add_argument("--url", required=True)
    parser.add_argument("--max_depth", type=int, default=250)
    
    args = parser.parse_args()
    
    if args.step == "initializing":
        run_initializing(args.url)
    elif args.step == "crawling":
        run_crawling(args.url, args.max_depth)
    elif args.step == "embedding":
        run_embedding(args.url)
    elif args.step == "indexing":
        run_indexing(args.url)
