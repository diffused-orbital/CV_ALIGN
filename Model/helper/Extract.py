from PyPDF2 import PdfReader
import docx

# To read PDF files
def read_pdf(file_path):
    text = ""
    try:
        with open(file_path,'rb') as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                text+=page.extract_text() or ""

    except Exception as e:
        print(f"Error reading PDF file: {e}")

    return text

# To read doc files
def read_docx(file_path):
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text+=para.text+"\n"

    except Exception as e:
        print(f"Error reading DOCX file: {e}")

    return text
