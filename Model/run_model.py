import os
from. helper import Extract_text as read, extract_jd_entity as jd, unified_cv_extraction as ext
from. helper import final_score as score

def read_resume_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        text = read.read_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        text = read.read_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return text

def read_job_description(job_folder):
    job_files = [f for f in os.listdir(job_folder) if f.endswith(('.pdf', '.docx', '.doc'))]
    if not job_files:
        raise FileNotFoundError("No job description file found in the job description folder!")
    job_file = os.path.join(job_folder, job_files[0])
    return read_resume_text(job_file)

def main(resume_folder, job_folder):
    # Step 1: Read job description
    job_text = read_job_description(job_folder)
    job_sections = jd.extract_job_details(job_text)

    # Step 2: Read and score resumes
    scores_list = []
    for file in os.listdir(resume_folder):
        if file.endswith(('.pdf', '.docx', '.doc')):
            file_path = os.path.join(resume_folder, file)
            resume_text = read_resume_text(file_path)
            resume_sections = ext.extract_resume_entities(resume_text)
            scores = score.score_resume(resume_sections, job_sections)
            final_score = scores.get('final_score', 0)
            scores_list.append({'file': file, 'final_score': final_score, 'scores': scores})

    # Step 3: Rank resumes by final score
    ranked_resumes = sorted(scores_list, key=lambda x: x['final_score'], reverse=True)

    # Step 4: Print rankings
    print("\nResume Rankings:")
    for idx, item in enumerate(ranked_resumes, start=1):
        print(f"{idx}. {item['file']} — Final Score: {item['final_score']:.2f}")

    return ranked_resumes
