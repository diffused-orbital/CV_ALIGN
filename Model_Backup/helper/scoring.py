from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
from . import synonym_mapping as syn

model = SentenceTransformer('all-MiniLM-L6-v2')

def flatten_to_text(sections):
    if isinstance(sections, dict):
        return ' '.join(flatten_to_text(v) for v in sections.values())
    elif isinstance(sections, list):
        return ' '.join(flatten_to_text(v) for v in sections)
    else:
        return str(sections)


def compute_tfidf_score(resume_text, job_text, synonym_mapping):
    resume_text = syn.apply_synonym_mapping(resume_text, synonym_mapping)
    job_text = syn.apply_synonym_mapping(job_text, synonym_mapping)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    return round(score, 4)


def compute_embedding_score(resume_text, job_text, synonym_mapping):
    resume_text = syn.apply_synonym_mapping(resume_text, synonym_mapping)
    job_text = syn.apply_synonym_mapping(job_text, synonym_mapping)

    embeddings = model.encode([resume_text, job_text], convert_to_tensor=True)
    score = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()

    return round(score, 4)


def compute_experience_score(resume_sections, job_sections, synonym_mapping):
    """
    Use experience first; fallback to projects if no experience.
    """
    experience_text = flatten_to_text(resume_sections.get('experience', {})).strip()
    if not experience_text:
        experience_text = flatten_to_text(resume_sections.get('projects', []))
    
    job_experience_text = flatten_to_text(job_sections.get('responsibilities', {}))

    experience_text = syn.apply_synonym_mapping(experience_text, synonym_mapping)
    job_experience_text = syn.apply_synonym_mapping(job_experience_text, synonym_mapping)

    embeddings = model.encode([experience_text, job_experience_text], convert_to_tensor=True)
    score = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()

    return round(score, 4)
