
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
INSTANCE_DIR = BACKEND_DIR / "instance"

# Load backend/.env for local development.
# In production, configure environment variables in the deployment platform.
load_dotenv(BACKEND_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(INSTANCE_DIR / 'app.db').as_posix()}",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Maximum total HTTP request size: 6 MB
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024

    # ID-card images use temporary files, not permanent storage.
    UPLOAD_FOLDER = None

    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://",
    )
    RATELIMIT_HEADERS_ENABLED = True
