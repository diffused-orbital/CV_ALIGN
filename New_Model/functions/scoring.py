import re
import os
# !pip install langchain_google_genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import extract_resume_sections as exres
import extract_jd_sections as exjd
import tokenize as tk
import others as ot
import pre_scoring as ps

def score_and_feedback(resume_sections: dict, jd_sections: dict, final_score: float) -> str:
    resume_text = '\n'.join([f"{sec}: {' '.join(words)}" for sec, words in resume_sections.items()])
    jd_text = '\n'.join([f"{sec}: {' '.join(words)}" for sec, words in jd_sections.items()])
    
    prompt_template = ChatPromptTemplate.from_template("""
You are a recruitment expert. Here is a resume and a job description.
Provide short, precise feedback listing strengths and weaknesses for this CV.
Do not consider formatting and structure as a weakness

Resume:
{resume_text}

Job Description:
{jd_text}

Score: {score:.2f}/100

Please provide:
Strengths: 
Weaknesses:
""")
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
    chain = prompt_template | llm | StrOutputParser()
    
    feedback = chain.invoke({
        "resume_text": resume_text,
        "jd_text": jd_text,
        "score": final_score
    })
    
    return feedback

# 8️⃣ Process all resumes and rank them
def process_resumes(resume_folder: str, jd_file: str) -> list:
    jd_text = exjd.read_job_description(jd_file)
    jd_sections = exjd.extract_job_details(jd_text)
    jd_sections_tokenized = tk.tokenize_sections(jd_sections)
    jd_text_flat = ' '.join([' '.join(words) for words in jd_sections_tokenized.values()])
    
    results = []
    #print(jd_sections_tokenized,"\n")
    for file in os.listdir(resume_folder):
        if file.lower().endswith(('.pdf', '.docx')):
            file_path = os.path.join(resume_folder, file)
            print(f"Processing: {file_path}")
            resume_text = exres.read_resume(file_path)
            resume_sections = exres.extract_sections(resume_text)
            resume_sections_tokenized = tk.tokenize_sections(resume_sections)
            resume_text_flat = ' '.join([' '.join(words) for words in resume_sections_tokenized.values()])
            
            embed_score = ps.embedding_score(resume_sections_tokenized, jd_sections_tokenized)
            tfidf = ps.tfidf_score(resume_text_flat, jd_text_flat)
            combined_text = resume_text_flat + ' ' + jd_text_flat
            synonym_mapping = ot.create_synonym_mapping(combined_text)
            exp_score = ps.experience_score(resume_sections,jd_sections, synonym_mapping)
            
            final_score = 0.5 * embed_score + 0.3 * tfidf + 0.2 * exp_score
            
            feedback = score_and_feedback(resume_sections_tokenized, jd_sections_tokenized, final_score)
            print("Embedding score: ",embed_score)
            print("TF-IDF score: ",tfidf)
            print("Experience score: ",exp_score)
            candidate_name = re.split('_CV', file, flags=re.IGNORECASE)[0]
            results.append({
                "Name": candidate_name,
                "Score": final_score,
                "Feedback": feedback
            })
    
    # Sort by final score
    results.sort(key=lambda x: x["Score"], reverse=True)
    return results
