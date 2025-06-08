import re

def extract_section(text, section_names, all_section_names):
   
    # Create regex pattern for section names (case-insensitive, possible synonyms)
    section_pattern = r'|'.join([re.escape(name) for name in section_names])
    all_sections_pattern = r'|'.join([re.escape(name) for name in all_section_names])

    # Find the start of the target section
    start_match = re.search(rf'({section_pattern})[:\s]*', text, re.I)
    if not start_match:
        return ""

    start_index = start_match.end()

    # Find the start of the next section after this one
    next_section_match = re.search(rf'({all_sections_pattern})[:\s]*', text[start_index:], re.I)
    if next_section_match:
        end_index = start_index + next_section_match.start()
    else:
        end_index = len(text)

    section_text = text[start_index:end_index].strip()
    section_text = re.sub(r'\n+', '\n', section_text)
    section_text = re.sub(r'\s+', ' ', section_text)
    return section_text.strip()


# All possible section names
ALL_SECTION_NAMES = [
    'skills', 'technical skills', 'core competencies',
    'experience', 'work experience', 'internships', 'employment history', 'professional experience',
    'projects', 'academic projects', 'personal projects',
    'courses', 'coursework', 'relevant courses', 'relevant coursework',
    'achievements', 'awards', 'honors', 'certifications', 'recognitions','por','position','responsibility'
]

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
