import os
import json
import boto3
import numpy as np
from botocore.exceptions import ClientError
from sentence_transformers import SentenceTransformer
from .dataset import Data

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
        """Save embeddings and the corresponding model.

        Args:
            path (str): folder for saving model and embeddings.
        """
        
        self.data.model.save(path + "embeddings_model")
        np.save(path + "embeddings", self.data.embeddings)


    def load_embeddings(self, path):
        """Load embeddings and the corresponding model.

        Args:
            path (str): folder for saving model and embeddings.
        """
        self.data.model = SentenceTransformer(path + "embeddings_model")
        self.data.embeddings = np.load(path + "embeddings.npy")


######################### AWS Files Operations ###########################
class AWSFileManager(FileManager):
    def __init__(self, data:Data, bucket_name, aws_access_key_id, aws_secret_access_key, region_name="ca-central-1"):
        super().__init__(data)
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.bucket_name = bucket_name

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