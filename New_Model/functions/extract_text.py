import os
import requests
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO

def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")

def extract_text_from_pdf(file_stream) -> str:
    reader = PdfReader(file_stream)
    text = ' '.join(page.extract_text() or '' for page in reader.pages)
    if not text.strip():
        raise ValueError('PDF has no readable text. Upload a text-based PDF.')
    return text

def extract_text_from_docx(file_stream) -> str:
    doc = Document(file_stream)
    return ' '.join([para.text for para in doc.paragraphs])

def read_resume(file_path: str) -> str:
    if is_url(file_path):
        response = requests.get(file_path, timeout=(10, 60))
        response.raise_for_status()
        content = response.content
        # Signed download URLs point at a /download endpoint with no file
        # extension, so fall back to sniffing the content's magic bytes
        # (PDF -> "%PDF", DOCX is a zip -> "PK").
        clean = file_path.split("?")[0].lower()
        if clean.endswith(".pdf") or content[:4] == b"%PDF":
            return extract_text_from_pdf(BytesIO(content))
        elif clean.endswith(".docx") or content[:2] == b"PK":
            return extract_text_from_docx(BytesIO(content))
        else:
            raise ValueError("Unsupported file type (from URL)")
    else:
        if file_path.lower().endswith(".pdf"):
            return extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            return extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file type (from disk)")

def read_job_description(file_path: str) -> str:
    return read_resume(file_path)
