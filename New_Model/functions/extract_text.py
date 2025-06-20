import os
import requests
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO

def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")

def extract_text_from_pdf(file_stream) -> str:
    reader = PdfReader(file_stream)
    text = ' '.join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

def extract_text_from_docx(file_stream) -> str:
    doc = Document(file_stream)
    return ' '.join([para.text for para in doc.paragraphs])

def read_resume(file_path: str) -> str:
    if is_url(file_path):
        response = requests.get(file_path)
        if file_path.lower().endswith(".pdf"):
            return extract_text_from_pdf(BytesIO(response.content))
        elif file_path.lower().endswith(".docx"):
            return extract_text_from_docx(BytesIO(response.content))
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
