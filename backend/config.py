from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or an .env file.

    Attributes:
        env (str): Short environment identifier (e.g., 'dev', 'prod').
        fireworks_api_key (str): API key for Fireworks service.
        model_embeddings_name (str): Embedding model identifier/name.
        model_llm_name (str): LLM model identifier/name.
        deployment_type (str): Deployment mode for the LLM (e.g., 'serverless').
        environment (str): Name of the .env file base (defaults to 'env').
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    env: str = Field(..., env="ENV")
    fireworks_api_key: str = Field(..., env="FIREWORKS_API_KEY")
    model_embeddings_name: str = Field(..., env="MODEL_EMBEDDINGS_NAME")
    model_llm_name: str = Field(..., env="MODEL_LLM_NAME")
    deployment_type: str = Field(..., env="DEPLOYMENT_TYPE")
    environment: str = Field("env", env="ENVIRONMENT")