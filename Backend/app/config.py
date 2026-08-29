"""Central configuration loaded from environment variables.

Secrets are read from a local .env file (see .env.example) so that no
credentials live in source control. Loading is anchored to the Backend
directory so it works regardless of the current working directory.
"""
import os
from pathlib import Path

import cloudinary
from dotenv import load_dotenv

# Backend/ directory (this file is Backend/app/config.py)
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

# Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Google Gemini (LangChain reads GOOGLE_API_KEY from the environment)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# JWT / auth
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def configure_cloudinary():
    """Apply Cloudinary credentials from the environment to the global client."""
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )
