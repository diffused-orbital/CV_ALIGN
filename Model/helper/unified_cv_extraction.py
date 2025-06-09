def extract_resume_entities(full_text):
    # Extract sections
    education_text = extract_education(full_text)
    experience_text = extract_experience(full_text)
    skills_text = extract_skills(full_text)
    achievements_text = extract_achievements(full_text)
    courses_text = extract_courses(full_text)
    projects_text = extract_projects(full_text)

    # Entity extraction
    education_data = extract_education_entities(education_text)
    experience_data = extract_experience_entities(experience_text)
    skills_list = extract_list_items(skills_text)
    achievements_list = extract_list_items(achievements_text)
    courses_list = extract_list_items(courses_text)
    projects_list = extract_list_items(projects_text)

    # Final dictionary
    return {
        "education": education_data,
        "experience": experience_data,
        "skills": skills_list,
        "achievements": achievements_list,
        "courses": courses_list,
        "projects": projects_list
    }