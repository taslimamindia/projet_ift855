from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Any

class Settings(BaseSettings):
    """Application configuration loaded from environment variables or a specified .env file."""

    env: str = Field(..., env="ENV")
    fireworks_api_key: str = Field(..., env="FIREWORKS_API_KEY")
    model_embeddings_name: str = Field(..., env="MODEL_EMBEDDINGS_NAME")
    model_llm_name: str = Field(..., env="MODEL_LLM_NAME")
    deployment_type: str = Field(..., env="DEPLOYMENT_TYPE")
    aws_access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(..., env="AWS_REGION")
    aws_s3_bucket_name_backend: str = Field(..., env="AWS_S3_BUCKET_NAME_BACKEND")
    base_prefix: str = Field("project_ift855/datasets/", env="BASE_PREFIX")
    clearml_web_host: str = Field(None, env="CLEARML_WEB_HOST")
    clearml_api_host: str = Field(None, env="CLEARML_API_HOST")
    clearml_files_host: str = Field(None, env="CLEARML_FILES_HOST")
    clearml_api_access_key: str = Field(None, env="CLEARML_API_ACCESS_KEY")
    clearml_api_secret_key: str = Field(None, env="CLEARML_API_SECRET_KEY")
    default_folder: str = Field("default_dataset", env="DEFAULT_FOLDER")

    model_config = {
        "protected_namespaces": ("settings_",)
    }


    def __str__(self):
        def mask(value: str, visible: int = 4) -> str:
            return value[:visible] + "..." if value else "None"

        return f"""
        Settings(
            env={self.env},
            fireworks_api_key={mask(self.fireworks_api_key)},
            model_embeddings_name={self.model_embeddings_name},
            model_llm_name={self.model_llm_name},
            deployment_type={self.deployment_type},
            aws_access_key_id={mask(self.aws_access_key_id)},
            aws_secret_access_key={mask(self.aws_secret_access_key)},
            aws_region={self.aws_region},
            aws_s3_bucket_name_backend={self.aws_s3_bucket_name_backend},
            base_prefix={self.base_prefix},
            clearml_web_host={self.clearml_web_host},
            clearml_api_host={self.clearml_api_host},
            clearml_files_host={self.clearml_files_host},
            clearml_api_access_key={mask(self.clearml_api_access_key)},
            clearml_api_secret_key={mask(self.clearml_api_secret_key)}
        )
        """

    @field_validator("fireworks_api_key", "aws_access_key_id", "aws_secret_access_key", mode="before")
    @classmethod
    def validate_not_empty(cls, v, info):
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v