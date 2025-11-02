import os
from config import Settings

# Determine which environment file to load. Default to `.env` when ENVIRONMENT is not set.
env = os.getenv("ENVIRONMENT", "env")
if env == "env":
    settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
else:
    # support providing a different env filename via the ENVIRONMENT variable
    settings = Settings(_env_file=f"{env}.env", _env_file_encoding="utf-8")