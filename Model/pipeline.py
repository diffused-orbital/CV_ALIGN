import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
import docx
import spacy

# Load a SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2') 
nlp = spacy.load("en_core_web_sm")

# Function to read a PDF file
def read_pdf(file_path):
    text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Function to read a DOCX file
def read_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Basic preprocessing function
def preprocess(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.strip().lower()
    return text

# Function to chunk text into sentences or paragraphs
def chunk_text(text, chunk_size=3):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = [' '.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
    return chunks

def extract_projects_from_resume(resume_text):
    """
    Extracts project descriptions from a plain text resume.

    Parameters:
        resume_text (str): Plain text of the resume.

    Returns:
        List of project descriptions (list of strings).
    """
    project_section_keywords = [
        'projects', 'academic projects', 'personal projects', 'professional projects'
    ]

    # Normalize text (lowercase, etc.)
    text = resume_text.lower()

    # Find potential project sections
    project_sections = []
    for keyword in project_section_keywords:
        pattern = rf"{keyword}.*"
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            start_idx = match.start()
            # Take a chunk of text after this keyword
            chunk = text[start_idx : start_idx + 1500]  # Adjust chunk size if needed
            project_sections.append(chunk)

    # Extract bullet points or numbered lists within project sections
    project_descriptions = []
    bullet_pattern = r"[-•*]\s*(.+)"
    numbered_pattern = r"\d+\.\s*(.+)"

    for section in project_sections:
        bullets = re.findall(bullet_pattern, section)
        project_descriptions.extend(bullets)

        numbered_items = re.findall(numbered_pattern, section)
        project_descriptions.extend(numbered_items)

    # As fallback, extract sentences containing 'project' keyword
    if not project_descriptions:
        sentences = re.split(r'[.?!]', text)
        for sent in sentences:
            if 'project' in sent:
                project_descriptions.append(sent.strip())

    # Clean up descriptions
    project_descriptions = [desc.strip().capitalize() for desc in project_descriptions if len(desc.strip()) > 20]

    return project_descriptions


def calculate_projects_score(projects, job_description, min_project_score=0.2):
    """
    Calculate the average similarity between project descriptions and job description.
    """
    job_embedding = model.encode(job_description, convert_to_tensor=True)

    project_scores = []
    for project in projects:
        project_embedding = model.encode(project, convert_to_tensor=True)
        sim_score = util.pytorch_cos_sim(job_embedding, project_embedding).item()
        # Ensure minimum project score
        sim_score = max(sim_score, min_project_score)
        project_scores.append(sim_score)

    if project_scores:
        return sum(project_scores) / len(project_scores)
    else:
        return min_project_score  # If no projects, still assign minimum

def calculate_experience_score(years_of_experience, project_descriptions, job_description):
    years_score = min(years_of_experience / 10, 1.0) 
    projects_score = calculate_projects_score(project_descriptions, job_description)

    if years_of_experience > 0:
        return 0.7 * years_score + 0.3 * projects_score
    else:
        return 0.3 * years_score + 0.7 * projects_score
# Dummy experience score parser (example using regex)
def extract_experience_score(text):
    match = re.findall(r'(\d+)\s*years?', text, re.I)
    if match:
        years = max([int(y) for y in match])
        return years 
    return 0

# Compute final weighted score
def compute_final_score(tfidf_score, embedding_score, experience_score):
    return 0.3 * tfidf_score + 0.5 * embedding_score + 0.2 * experience_score

# Main function to score CVs against the job description
def score_cvs(job_desc_file, cv_files, top_k=5):
    if job_desc_file.endswith(".pdf"):
        job_desc = read_pdf(job_desc_file)
    elif job_desc_file.endswith(".docx"):
        job_desc = read_docx(job_desc_file)
    else:
        with open(job_desc_file, 'r', encoding='utf-8') as f:
            job_desc = f.read()

    job_desc = preprocess(job_desc)

    # Generate embedding for job description
    job_embedding = model.encode(job_desc, convert_to_tensor=True)
    # TF-IDF vectorizer initialization
    all_texts = [job_desc]
    # Read and preprocess CVs
    cv_chunks_list = []
    cv_raw_texts = []
    for file in cv_files:
        if file.endswith(".pdf"):
            text = read_pdf(file)
        elif file.endswith(".docx"):
            text = read_docx(file)
        else:
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
        text = preprocess(text)
        chunks = chunk_text(text)
        cv_chunks_list.append(chunks)
        cv_raw_texts.append(text)
        all_texts.extend(chunks)

    # Compute TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # TF-IDF similarity between job description and each chunk
    job_tfidf = tfidf_matrix[0]
    cv_scores = []
    for i, chunks in enumerate(cv_chunks_list):
        chunk_indices = range(1 + sum(len(c) for c in cv_chunks_list[:i]),
                               1 + sum(len(c) for c in cv_chunks_list[:i+1]))
        chunk_tfidfs = tfidf_matrix[chunk_indices]
        # Compute cosine similarity
        similarities = (chunk_tfidfs * job_tfidf.T).toarray().flatten()
        tfidf_score = max(similarities)

        # Embedding similarity
        chunk_embeddings = model.encode(chunks, convert_to_tensor=True)
        similarities = util.cos_sim(job_embedding, chunk_embeddings).flatten()
        # Extract top K
        top_k_indices = similarities.argsort(descending=True)[:top_k]
        embedding_score = float(similarities[top_k_indices].mean())

        # Experience score
        years_of_experience = extract_experience_score(cv_raw_texts[i])
        project_descriptions = extract_projects_from_resume(cv_raw_texts[i])
        exp_score = calculate_experience_score(years_of_experience, project_descriptions, cv_raw_texts[i])

        # Final score
        final_score = compute_final_score(tfidf_score, embedding_score, exp_score)

        cv_scores.append({
            "file": cv_files[i],
            "tfidf_score": tfidf_score,
            "embedding_score": embedding_score,
            "experience_score": exp_score,
            "final_score": final_score
        })

    # Sort by final score
    cv_scores.sort(key=lambda x: x['final_score'], reverse=True)
    return cv_scores

# Example usage:
if __name__ == "__main__":
    # job_desc_file = "/content/ML_Internship_Job_Description.pdf"
    # cv_files = ["/content/Arnav_Tiku_CV.pdf", "/content/HimaniGupta_Resume.pdf", "/content/resume 2.0.pdf","/content/Pranjay_Kapoor_CV (2).pdf","/content/Resume_Simran L&D.pdf"]

    rankings = score_cvs(job_desc_file, cv_files, top_k=5)
    for rank, cv in enumerate(rankings, start=1):
        print(f"Rank {rank}: {cv['file']}")
        print(f"  Final Score: {cv['final_score']:.4f}")
        print(f"  TF-IDF Score: {cv['tfidf_score']:.4f}")
        print(f"  Embedding Score: {cv['embedding_score']:.4f}")
        print(f"  Experience Score: {cv['experience_score']:.4f}\n")
