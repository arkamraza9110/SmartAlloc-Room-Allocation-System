"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "smartalloc_db")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

