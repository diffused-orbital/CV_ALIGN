import extract_cv_sections as sect
import extract_cv_entity as ent

def extract_resume_entities(full_text):
    # Extract sections
    education_text = sect.extract_education(full_text)
    experience_text = sect.extract_experience(full_text)
    skills_text = sect.extract_skills(full_text)
    achievements_text = sect.extract_achievements(full_text)
    courses_text = sect.extract_courses(full_text)
    projects_text = sect.extract_projects(full_text)

    # Entity extraction
    education_data = ent.extract_education_entities(education_text)
    experience_data = ent.extract_experience_entities(experience_text)
    skills_list = ent.extract_list_items(skills_text)
    achievements_list = ent.extract_list_items(achievements_text)
    courses_list = ent.extract_list_items(courses_text)
    projects_list = ent.extract_list_items(projects_text)

    # Final dictionary
    return {
        "education": education_data,
        "experience": experience_data,
        "skills": skills_list,
        "achievements": achievements_list,
        "courses": courses_list,
        "projects": projects_list
    }