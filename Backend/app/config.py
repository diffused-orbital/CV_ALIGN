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
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if len(JWT_SECRET_KEY) < 32 or JWT_SECRET_KEY in {
    "dev-insecure-secret-change-me", "change-me-to-a-long-random-string"
}:
    raise RuntimeError("Set JWT_SECRET_KEY to a randomly generated secret of at least 32 characters.")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
SMTP_FROM = os.getenv("SMTP_FROM", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def configure_cloudinary():
    """Apply Cloudinary credentials from the environment to the global client."""
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )
