import os
from pathlib import Path
from config import Settings
import logging
from dotenv import load_dotenv


_uvicorn_logger = logging.getLogger("uvicorn.error")
logger = _uvicorn_logger if _uvicorn_logger.handlers else logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
env = os.getenv("ENV", None)
logger.info(f"Environment variable ENV: {env}")

candidate = None
if env == "env":
    candidate = BASE_DIR / ".env"
elif env == "prod":
    candidate = BASE_DIR / "prod.env"
else:
    load_dotenv()

env_file_path = None
if candidate and candidate.exists():
    env_file_path = candidate

if env_file_path:
    logger.info(f"Loading settings from env file: {env_file_path}")
    settings = Settings(_env_file=str(env_file_path), _env_file_encoding="utf-8")
    logger.info(f"Loaded settings from env file: {env_file_path}")
else:
    settings = Settings()
    logger.info("No env file found; loaded settings from OS environment variables.")