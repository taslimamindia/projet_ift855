import os
import json
import boto3
import numpy as np
from botocore.exceptions import ClientError
from .dataset import Data
import json
from langchain_core.documents import Document


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
    def __init__(self, data:Data, bucket_name, aws_access_key_id, aws_secret_access_key, base_prefix, region_name="ca-central-1"):
        super().__init__(data)
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.bucket_name = bucket_name
        self.base_prefix = base_prefix.rstrip("/") + "/" if base_prefix else ""

    def create_folder_in_aws(self, folder):
        """
        Creates an empty folder (prefix) in S3.

        Args:
        - folder: folder name to create (e.g. 'documents/')
        """
        self.s3.put_object(Bucket=self.bucket_name, Key=f"{folder}/")

    def rename_folder_in_aws(self, old_folder, new_folder):
        """
        Renames a folder by copying all objects to a new prefix and deleting the old ones.

        Args:
        - old_folder: current folder prefix (e.g. 'documents/')
        - new_folder: new folder prefix (e.g. 'archives/')
        """
        objects = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=old_folder)
        for obj in objects.get('Contents', []):
            old_key = obj['Key']
            new_key = old_key.replace(old_folder, new_folder, 1)
            self.s3.copy_object(Bucket=self.bucket_name, CopySource={'Bucket': self.bucket_name, 'Key': old_key}, Key=new_key)
            self.s3.delete_object(Bucket=self.bucket_name, Key=old_key)

    def delete_folder_in_aws(self, folder):
        """
        Deletes all objects within a given folder (prefix) in S3.

        Args:
        - folder: folder prefix to delete (e.g. 'documents/')
        """
        objects = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=folder)
        for obj in objects.get('Contents', []):
            self.s3.delete_object(Bucket=self.bucket_name, Key=obj['Key'])

    def upload_file_in_aws(self, key, content):
        """
        Uploads a file to S3.

        Args:
        - key: full S3 path for the file (e.g. 'documents/report.txt')
        - content: file content as string or bytes
        """
        self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=content)

    def rename_file_in_aws(self, old_key, new_key):
        """
        Renames a file in S3 by copying and deleting the original.

        Args:
        - old_key: current file path (e.g. 'documents/old.txt')
        - new_key: new file path (e.g. 'documents/new.txt')
        """
        self.s3.copy_object(Bucket=self.bucket_name, CopySource={'Bucket': self.bucket_name, 'Key': old_key}, Key=new_key)
        self.s3.delete_object(Bucket=self.bucket_name, Key=old_key)

    def update_file_in_aws(self, key, new_content):
        """
        Overwrites the content of an existing file in S3.

        Args:
        - key: file path in S3 (e.g. 'documents/report.txt')
        - new_content: new content to write
        """
        self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=new_content)

    def delete_file_in_aws(self, key):
        """
        Deletes a file from S3.

        Args:
        - key: file path to delete (e.g. 'documents/report.txt')
        """
        self.s3.delete_object(Bucket=self.bucket_name, Key=key)

    def read_file_from_aws(self, key):
        """
        Reads the content of a file stored in S3.

        Args:
        - key: file path to read (e.g. 'documents/report.txt')
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            print(f"Content of '{key}':\n{content}")
            return content
        except Exception as e:
            print(f"Error reading file '{key}': {e}")
            return None

    def list_folder_from_aws(self, prefix):
        """
        Lists all files within a given folder (prefix) in S3.

        Args:
        - prefix: folder prefix to list (e.g. 'documents/')
        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            files = [obj['Key'] for obj in response.get('Contents', [])]
            print(f"Files in folder '{prefix}':")
            for f in files:
                print(f" - {f}")
            return files
        except Exception as e:
            print(f"Error listing folder '{prefix}': {e}")
            return []

    def download_file_from_aws(self, aws_path, local_path):
        """
        Downloads a single file from S3 to local disk.

        Args:
        - aws_path: full S3 path of the file (e.g. 'documents/report.txt')
        - local_path: local path to save the file (e.g. './report.txt')
        """
        try:
            self.s3.download_file(self.bucket_name, aws_path, local_path)
            print(f"Downloaded: {aws_path} → {local_path}")
        except Exception as e:
            print(f"Error downloading '{aws_path}': {e}")

    def download_folder_from_aws(self, folder, local_folder):
        """
        Downloads all files from a given S3 folder (prefix) to a local directory.

        Args:
        - folder: S3 folder prefix (e.g., 'documents/')
        - local_folder: local path to save the files (e.g. './dossiers/')
        """
        try:
            os.makedirs(local_folder, exist_ok=True)

            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=folder)
            objects = response.get('Contents', [])

            for obj in objects:
                key = obj['Key']
                
                if key.endswith('//'): 
                    continue

                if key.endswith('/'):
                    os.makedirs(local_folder + key, exist_ok=True)
                    continue

                filename = os.path.basename(key)
                local_path = os.path.join(local_folder + key.replace(filename, ''), filename)
                self.s3.download_file(self.bucket_name, key, local_path)
                print(f"Downloaded: {key} → {local_path}")
        
        except ClientError as e:
            print(f"AWS error: {e.response['Error']['Code']} — {e.response['Error']['Message']}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def upload_file(self, local_path: str, s3_key: str = None) -> str:
        """Upload a single local file to S3
        
        Args:
            local_path (str): Path to the local file to upload.
            s3_key (str, optional): S3 key (path) for the uploaded file. If None, uses the local filename. Defaults to None.
        Returns:
            str: S3 URL of the uploaded file.
        """

        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        if s3_key is None:
            s3_key = os.path.basename(local_path)

        full_key = self.base_prefix + s3_key

        try:
            self.s3.upload_file(local_path, self.bucket_name, full_key)
        except ClientError as e:
            print(f"Error uploading file to S3: {e}")
            raise e

    def upload_folder(self, folder_path: str) -> list:
        """Upload an entire local folder (recursively) to S3
        
        Args:
            folder_path (str): Path to the local folder to upload.
        Returns:
            list: List of S3 URLs of the uploaded files.
        """

        if not os.path.isdir(folder_path):
            raise NotADirectoryError(f"Directory not found: {folder_path}")

        uploaded_urls = []

        for root, _, files in os.walk(folder_path):
            for filename in files:
                local_file_path = os.path.join(root, filename)
                # Keep folder structure on S3
                relative_path = os.path.relpath(local_file_path, folder_path)
                s3_key = self.base_prefix + relative_path.replace("\\", "/")

                try:
                    self.s3.upload_file(local_file_path, self.bucket_name, s3_key)
                    file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
                    uploaded_urls.append(file_url)
                except ClientError as e:
                    print(f"Error uploading {filename}: {e}")

        return uploaded_urls
    

    def load_json_documents_from_s3(self, key: str) -> list[Document]:
        """
        Load JSON data from an S3 bucket where each key is a URL and each value is the corresponding document text.

        The function connects to AWS S3, downloads a JSON file, parses it, and converts each (URL, text)
        pair into a LangChain Document object.

        Args:
            bucket_name (str): The name of the S3 bucket.
            key (str): The full path (key) to the JSON file in the bucket.
            aws_access_key_id (str): AWS access key ID for authentication.
            aws_secret_access_key (str): AWS secret access key for authentication.

        Returns:
            list[Document]: A list of LangChain Document objects, each representing a URL-text pair.
        """
        

        obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
        file_content = obj["Body"].read().decode("utf-8")

        data = json.loads(file_content)

        documents = [
            Document(page_content=text, metadata={"source": url})
            for url, text in data.items()
        ]

        return documents
