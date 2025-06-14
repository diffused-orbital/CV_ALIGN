# !pip install PyPDF2
# !pip install python-docx
from PyPDF2 import PdfReader
from docx import Document
# Extract text from PDF and DOCX
def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ' '.join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return ' '.join([para.text for para in doc.paragraphs])

def read_resume(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type")

def read_job_description(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type")
