import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
from . import others as ot  

def generate_embeddings(texts: list) -> np.ndarray:
    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    embeddings = embeddings_model.embed_documents(texts)
    return np.array(embeddings)

def embedding_score(resume_sections: dict, jd_sections: dict) -> float:
    resume_text = ' '.join([' '.join(words) for words in resume_sections.values()])
    jd_text = ' '.join([' '.join(words) for words in jd_sections.values()])
    embeddings = generate_embeddings([resume_text, jd_text])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return similarity * 100

# 5️⃣ TF-IDF score
def tfidf_score(resume_text: str, jd_text: str) -> float:
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return score * 100

# 6️⃣ Experience/Project score
   
model = SentenceTransformer('all-MiniLM-L6-v2')
def experience_score(resume_sections, job_sections, synonym_mapping):
    """
    Use experience first; fallback to projects if no experience.
    """
    experience_text = ot.flatten_to_text(resume_sections.get('experience', {})).strip()
    if not experience_text:
        experience_text = ot.flatten_to_text(resume_sections.get('projects', []))
    
    job_experience_text = ot.flatten_to_text(job_sections.get('responsibilities', {}))

    experience_text = ot.apply_synonym_mapping(experience_text, synonym_mapping)
    job_experience_text = ot.apply_synonym_mapping(job_experience_text, synonym_mapping)

    embeddings = model.encode([experience_text, job_experience_text], convert_to_tensor=True)
    score = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()


    return round(score, 4)