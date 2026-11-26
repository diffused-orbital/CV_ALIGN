import logging
import re
import time
import uuid
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

import cloudinary.uploader
import cloudinary.utils
import requests
from fastapi import HTTPException
from PyPDF2 import PdfReader

from app.config import CLOUDINARY_CLOUD_NAME, configure_cloudinary

MAX_PDF_BYTES = 10 * 1024 * 1024
logger = logging.getLogger(__name__)


def validate_pdf(content):
    if not content or len(content) > MAX_PDF_BYTES:
        raise HTTPException(413, "PDF files must be between 1 byte and 10 MB.")
    try:
        if not content.startswith(b"%PDF-"):
            raise ValueError("Missing PDF header")
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted or not reader.pages:
            raise ValueError("Encrypted or empty PDF")
        # Load the page trees before accepting the file.
        for page in reader.pages:
            _ = page.mediabox
    except Exception as exc:
        raise HTTPException(400, "Upload a valid, unencrypted PDF with at least one page.") from exc
    return content


def upload_pdf(file, prefix):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed.")
    content = validate_pdf(file.file.read(MAX_PDF_BYTES + 1))
    return upload_pdf_bytes(content, prefix)


def upload_pdf_bytes(content, prefix):
    configure_cloudinary()
    public_id = f"{prefix}/{uuid.uuid4()}.pdf"
    try:
        result = cloudinary.uploader.upload(
            BytesIO(content), resource_type="raw", type="authenticated",
            public_id=public_id, overwrite=False,
        )
    except Exception as exc:
        raise HTTPException(502, "Document storage is unavailable. Please try again.") from exc
    # Authenticated uploads include a permanent signature in secure_url.
    # Store an unsigned asset reference and issue expiring downloads separately.
    return re.sub(r"/s--[A-Za-z0-9_-]+--/", "/", result["secure_url"])


def cloudinary_asset_reference(url):
    parsed = urlparse(url)
    parts = [unquote(part) for part in parsed.path.split("/") if part]
    if parsed.scheme != "https" or parsed.hostname != "res.cloudinary.com" or not parts or parts[0] != CLOUDINARY_CLOUD_NAME:
        raise ValueError("The stored document is not in the configured Cloudinary account.")
    try:
        index = parts.index("raw")
        delivery_type = parts[index + 1]
        asset_parts = parts[index + 2:]
    except (ValueError, IndexError) as exc:
        raise ValueError("The stored document is not a Cloudinary raw file.") from exc
    if delivery_type not in {"upload", "authenticated", "private"}:
        raise ValueError("Unsupported Cloudinary delivery type.")
    if asset_parts and re.fullmatch(r"s--[A-Za-z0-9_-]+--", asset_parts[0]):
        asset_parts = asset_parts[1:]
    if asset_parts and re.fullmatch(r"v\d+", asset_parts[0]):
        asset_parts = asset_parts[1:]
    if not asset_parts or PurePosixPath(asset_parts[-1]).suffix.lower() != ".pdf":
        raise ValueError("The stored document is not a PDF.")
    return "/".join(asset_parts), None, delivery_type


def signed_download_url(url, attachment=False):
    public_id, file_format, delivery_type = cloudinary_asset_reference(url)
    configure_cloudinary()
    return cloudinary.utils.private_download_url(
        public_id, file_format, resource_type="raw", type=delivery_type,
        attachment=attachment, expires_at=int(time.time()) + 300,
    )


def download_pdf(url):
    try:
        signed_url = signed_download_url(url)
        with requests.get(signed_url, timeout=(10, 60), stream=True, allow_redirects=False) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(65536):
                content.extend(chunk)
                if len(content) > MAX_PDF_BYTES:
                    raise HTTPException(413, "Stored PDF exceeds 10 MB.")
        return validate_pdf(bytes(content))
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(502, "The stored PDF could not be retrieved from Cloudinary.") from exc


def delete_uploaded_pdf(url):
    """Compensate an upload when its database transaction cannot be committed."""
    try:
        public_id, _, delivery_type = cloudinary_asset_reference(url)
        configure_cloudinary()
        cloudinary.uploader.destroy(public_id, resource_type="raw", type=delivery_type, invalidate=True)
    except Exception:
        logger.error("Could not clean up a document after a failed database transaction.")
