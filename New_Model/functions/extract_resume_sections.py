import re
def extract_section(text, section_names, all_section_names):
    # Create regex pattern for section names
    section_pattern = r'|'.join([re.escape(name) for name in section_names])
    # Find the start of the target section
    start_match = re.search(rf'({section_pattern})[:\s]*', text, re.I)
    if not start_match:
        return ""
    start_index = start_match.end()
    
    # Split text into words
    tokens = re.split(r'(\s+)', text[start_index:])  # \s+ separator preserved as tokens
    collected_tokens = []
    i = 0
    while i < len(tokens):
        word = tokens[i].strip().lower()
        if word in all_section_names and word not in section_names:
            break
        collected_tokens.append(tokens[i])
        i += 1
    
    section_text = ''.join(collected_tokens).strip()
    
    # Cleanup
    section_text = re.sub(r'\n+', '\n', section_text)
    section_text = re.sub(r'\s+', ' ', section_text)
    return section_text.strip()

ALL_SECTION_NAMES = [
    'skills', 'technical skills', 'core competencies',
    'experience', 'work experience', 'internships', 'employment history', 'professional experience',
    'projects', 'academic projects', 'personal projects',
    'courses', 'coursework', 'relevant courses', 'relevant coursework',
    'achievements', 'awards', 'honors', 'certifications', 'recognitions', 'por', 'position', 'responsibility',
    'extracurriculars'
]

# def extract_education(text):
#     section_names = ['education', 'academic background', 'educational qualifications', 'qualifications', 'academic qualifications']
#     return extract_section(text, section_names, ALL_SECTION_NAMES)

def extract_skills(text):
    section_names = ['skills', 'technical skills', 'core competencies']
    return extract_section(text, section_names, ALL_SECTION_NAMES)

def extract_experience(text):
    section_names = ['experience', 'work experience', 'internships', 'employment history', 'professional experience']
    return extract_section(text, section_names, ALL_SECTION_NAMES)

def extract_projects(text):
    section_names = ['projects', 'academic projects', 'personal projects']
    return extract_section(text, section_names, ALL_SECTION_NAMES)

def extract_courses(text):
    section_names = ['courses', 'coursework', 'relevant courses', 'relevant coursework']
    return extract_section(text, section_names, ALL_SECTION_NAMES)

def extract_achievements(text):
    section_names = ['achievements', 'awards', 'honors', 'certifications', 'recognitions']
    return extract_section(text, section_names, ALL_SECTION_NAMES)

def extract_sections(text: str) -> dict:
    sections = {
        # "education": extract_education(text),
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "projects": extract_projects(text),
        "courses": extract_courses(text),
        "achievements" : extract_achievements(text)
    }
    # Remove empty sections
    # sections = {k: v for k, v in sections.items() if v.strip()}
    # print(sections,"\n\n")
    return sections