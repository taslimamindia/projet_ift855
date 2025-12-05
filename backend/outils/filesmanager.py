import os
import json
import boto3
import numpy as np
from botocore.exceptions import ClientError
from .dataset import Data
import json
from langchain_core.documents import Document
import tempfile
from typing import Literal
import logging


# Prefer uvicorn's logger when running under uvicorn; fall back to module logger
_uvicorn_logger = logging.getLogger("uvicorn.error")
logger = _uvicorn_logger if _uvicorn_logger.handlers else logging.getLogger(__name__)



######################## Files Operations ###############################
class FileManager:
    def __init__(self, data:Data):
        self.data = data


    def save_texts_to_json(self, texts, filename='crawled_data.json'):
        """Save a dictionary of texts to a JSON file.

        Args:
            texts (dict): Dictionary containing texts to save.
            filename (str, optional): Path to the JSON file. Defaults to 'crawled_data.json'.
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(texts, f, ensure_ascii=False, indent=4)


    def load_texts_from_json(self, filename='crawled_data.json'):
        """Load texts from a JSON file.

        Args:
            filename (str, optional): Path to the JSON file. Defaults to 'crawled_data.json'.

        Returns:
            dict: Dictionary containing the loaded texts.
        """

        with open(filename, 'r', encoding='utf-8') as f:
            texts = json.load(f)
        
        return texts


    def save_embeddings(self, path):
        """Save embeddings numpy array to the given folder path.

        Args:
            path (str): Folder path (will be used as a prefix). Example: './datasets/'.
        """
        
        np.save(path + "embeddings", self.data.embeddings)


    def load_embeddings(self, path):
        """Load embeddings numpy array from the specified folder path.

        Args:
            path (str): Folder path where 'embeddings.npy' is located (e.g., './datasets/').
        """
        self.data.embeddings = np.load(path + "embeddings.npy")


######################### AWS Files Operations ###########################
class AWSFileManager(FileManager):
    def __init__(self, data:Data, 
                 aws_s3_bucket_name, aws_access_key_id, 
                 aws_secret_access_key, 
                 base_prefix, 
                 aws_region="ca-central-1"):
        super().__init__(data)
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )
        self.bucket_name = aws_s3_bucket_name
        self.base_prefix = base_prefix.rstrip("/") + "/" if base_prefix else ""

    def create_folder_in_aws(self, folder, recreate: bool = False) -> bool:
        """
        Create a "folder" (prefix) in S3.

        Args:
            folder (str): folder name (e.g. 'documents' or 'documents/').
            recreate (bool): if True and the folder exists, delete its contents then recreate it.
                             if False and the folder exists, do nothing.

        Returns:
            bool: True if the folder was created (or recreated), False if the folder existed and was not recreated.
        """
        # Build S3 path including the base prefix
        path = self.base_prefix + folder.rstrip('/') + '/'

        try:
            # Check if there is at least one object with this prefix
            resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=path, MaxKeys=1)
            exists = 'Contents' in resp and len(resp['Contents']) > 0

            if exists and not recreate:
                # Folder exists and we don't want to recreate it
                return True

            if exists and recreate:
                # Delete all objects under this prefix (paged)
                paginator = self.s3.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=self.bucket_name, Prefix=path):
                    objs = page.get('Contents', [])
                    if not objs:
                        continue
                    delete_keys = [{'Key': o['Key']} for o in objs]
                    # delete_objects accepts up to 1000 objects per call
                    for i in range(0, len(delete_keys), 1000):
                        chunk = delete_keys[i:i + 1000]
                        self.s3.delete_objects(Bucket=self.bucket_name, Delete={'Objects': chunk})

            # Create a "placeholder" object to represent the folder
            self.s3.put_object(Bucket=self.bucket_name, Key=path)
            self.base_prefix = self.base_prefix + (folder.rstrip('/') + '/' if folder else "")
            return True

        except ClientError as e:
            logger.error(f"AWS error creating folder '{path}': {e.response.get('Error', {}).get('Message', str(e))}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error creating folder '{path}': {e}")
            raise

    def upload_file_in_aws(self, key: str, 
            content: list | str | bytes | dict | np.ndarray, 
            type_file: "Literal['json','txt','csv','npy','pdf','png','jpg','jpeg','bin']") -> bool | str:
        """
        Uploads a file to S3 by first writing a temporary local file, then uploading that file.
        The temporary file is removed only if the upload succeeds.

        Args:
        - key: full S3 path for the file relative to base_prefix (e.g. 'documents/report.txt' or '/documents/report.txt')
        - content: file content as string, bytes, dict (for json) or numpy array (for .npy)
        - type_file: optional single-type restriction as a string literal (e.g. "json", "txt", "npy").
                     If provided it forces/validates the file type. If None, the type is inferred from the key extension.
        """

        _, ext = os.path.splitext(key)
        ext = ext.lstrip(".").lower() if ext else None

        supported = {"json", "txt", "csv", "npy", "pdf", "png", "jpg", "jpeg", "bin"}

        detected_type = None
        if type_file:
            norm = type_file.strip().lstrip(".").lower()
            if norm not in supported:
                raise ValueError(f"type_file '{type_file}' not supported. Supported: {sorted(list(supported))}")
            if ext and ext != norm:
                raise ValueError(f"Provided type_file '{norm}' does not match file extension '{ext}'")
            detected_type = norm
        else:
            detected_type = ext

        # Build full_key (keep existing behavior but show debug)
        full_key = ((self.base_prefix.rstrip("/") + "/" if key else "") or "") + key + f".{detected_type}"

        content_type_map = {
            "json": "application/json",
            "txt": "text/plain; charset=utf-8",
            "csv": "text/csv",
            "npy": "application/octet-stream",
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "bin": "application/octet-stream",
        }
        content_type = content_type_map.get(detected_type, "application/octet-stream")

        # Create temporary file with appropriate suffix
        suffix = f".{detected_type}" if detected_type else ""
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

        try:
            # Write content to temp file according to type
            if detected_type == "json":
                if isinstance(content, (dict, list)):
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        json.dump(content, f, ensure_ascii=False)
                elif isinstance(content, str):
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.write(content)
                elif isinstance(content, bytes):
                    with open(tmp_path, "wb") as f:
                        f.write(content)
                else:
                    raise TypeError("For json, content must be dict/list, str or bytes.")
            elif detected_type in {"txt", "csv"}:
                if isinstance(content, bytes):
                    with open(tmp_path, "wb") as f:
                        f.write(content)
                else:
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.write(str(content))
            elif detected_type == "npy":
                if isinstance(content, np.ndarray):
                    # np.save accepts filename
                    np.save(tmp_path, content, allow_pickle=False)
                elif isinstance(content, bytes):
                    with open(tmp_path, "wb") as f:
                        f.write(content)
                else:
                    raise TypeError("For npy, content must be a numpy.ndarray or bytes.")
            else:
                # binary/image/pdf or generic
                if isinstance(content, bytes):
                    with open(tmp_path, "wb") as f:
                        f.write(content)
                else:
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.write(str(content))

            # Upload the temporary file to S3
            try:
                self.s3.upload_file(tmp_path, self.bucket_name, full_key, ExtraArgs={"ContentType": content_type})
                logger.debug(f"[DEBUG] upload succeeded for s3://{self.bucket_name}/{full_key}")
                # On success, remove the temporary file
                try:
                    os.remove(tmp_path)
                except Exception:
                    # If cleanup fails, don't fail the upload — just warn
                    logger.warning(f"Warning: failed to remove temporary file {tmp_path}")
                return True
            except ClientError as e:
                # Do not remove temp file; keep it for inspection
                raise ValueError(f"AWS error uploading file '{full_key}': {e.response.get('Error', {}).get('Message', str(e))}")
        finally:
            # In case writing failed before upload, ensure temp file is removed
            # Only remove if it still exists and upload wasn't attempted/succeeded.
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    raise ValueError(f"[DEBUG] final cleanup failed for {tmp_path}")

    def download_file_from_aws(self, key: str,
            type_file: "Literal['json','txt','csv','npy','pdf','png','jpg','jpeg','bin']") -> list | str | bytes | dict | np.ndarray:
        """
        Downloads a file from S3 and loads its content into memory.

        Args:
        - key: full S3 path for the file relative to base_prefix (e.g. 'documents/report.txt' or '/documents/report.txt')
        - type_file: expected file type as a string literal (e.g. "json", "txt", "npy").

        Returns:
        - content: file content as string, bytes, dict (for json) or numpy array (for .npy)
        """

        _, ext = os.path.splitext(key)
        ext = ext.lstrip(".").lower() if ext else None

        supported = {"json", "txt", "csv", "npy", "pdf", "png", "jpg", "jpeg", "bin"}

        detected_type = None
        if type_file:
            norm = type_file.strip().lstrip(".").lower()
            if norm not in supported:
                raise ValueError(f"type_file '{type_file}' not supported. Supported: {sorted(list(supported))}")
            if ext and ext != norm:
                raise ValueError(f"Provided type_file '{norm}' does not match file extension '{ext}'")
            detected_type = norm
        else:
            detected_type = ext

        # Build full_key
        full_key = ((self.base_prefix.rstrip("/") + "/" if key else "") or "") + key + f".{detected_type}"
        logger.debug(f"[DEBUG] download_file_from_aws full_key: {full_key}")

        try:
            # Download the file to a temporary location
            fd, tmp_path = tempfile.mkstemp()
            os.close(fd)
            self.s3.download_file(self.bucket_name, full_key, tmp_path)

            # Load content based on type_file
            if type_file == "json":
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
            elif type_file in {"txt", "csv"}:
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif type_file == "npy":
                content = np.load(tmp_path)
            else:
                with open(tmp_path, 'rb') as f:
                    content = f.read()

            # Clean up temporary file
            os.remove(tmp_path)
            return content

        except ClientError as e:
            logger.error(f"AWS error downloading file '{full_key}': {e.response.get('Error', {}).get('Message', str(e))}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error downloading file '{full_key}': {e}")
            raise