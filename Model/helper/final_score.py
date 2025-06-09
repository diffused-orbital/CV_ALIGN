import scoring as sc
import synonym_mapping as syn

def compute_final_score(tfidf_score, embedding_score, experience_score,
                        weights={'tfidf': 0.3, 'embedding': 0.5, 'experience': 0.2}):
    final = (
        weights['tfidf'] * tfidf_score +
        weights['embedding'] * embedding_score +
        weights['experience'] * experience_score
    )
    return round(final, 4)


def score_resume(resume_sections, job_sections):
    # Flatten texts
    resume_text = sc.flatten_to_text(resume_sections)
    job_text = sc.flatten_to_text(job_sections)

    # Create synonym mapping
    combined_text = resume_text + ' ' + job_text
    synonym_mapping = syn.create_synonym_mapping(combined_text)

    # Compute scores
    tfidf_score = sc.compute_tfidf_score(resume_text, job_text, synonym_mapping)
    embedding_score = sc.compute_embedding_score(resume_text, job_text, synonym_mapping)
    experience_score = sc.compute_experience_score(resume_sections, job_sections, synonym_mapping)
    final_score = compute_final_score(tfidf_score, embedding_score, experience_score)

    return {
        'tfidf_score': tfidf_score,
        'embedding_score': embedding_score,
        'experience_score': experience_score,
        'final_score': final_score
    }
