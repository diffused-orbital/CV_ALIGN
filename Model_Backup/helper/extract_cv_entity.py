import re
import spacy
nlp = spacy.load("en_core_web_sm")

def extract_education_entities(education_text):
    doc = nlp(education_text)
    degrees = []
    institutes = []
    grades = []

    degree_keywords = ['bachelor', 'master', 'phd', 'b.sc', 'm.sc', 'b.tech', 'm.tech', 'mba', 'msc', 'bca', 'mca']
    for line in education_text.split('\n'):
        for word in degree_keywords:
            if word in line.lower():
                degrees.append(line.strip())

    for ent in doc.ents:
        if ent.label_ in ['ORG', 'FAC']:
            institutes.append(ent.text)
        elif ent.label_ == 'PERCENT' or re.search(r'(cgpa|gpa|grade|percentage)', ent.text.lower()):
            grades.append(ent.text)

    grade_pattern = r'(?:cgpa|gpa|grade|percentage)\s*[:\-]?\s*[\d.]+'
    grades_found = re.findall(grade_pattern, education_text, re.I)
    if grades_found:
        grades.extend([g.strip() for g in grades_found])

    return {
        "degrees": list(set(degrees)),
        "institutes": list(set(institutes)),
        "grades": grades
    }

def extract_experience_entities(experience_text):
    doc = nlp(experience_text)
    companies = []
    roles = []
    durations = []

    role_keywords = ['intern', 'developer', 'manager', 'engineer', 'analyst', 'consultant', 'assistant', 'researcher', 'scientist']
    for line in experience_text.split('\n'):
        for word in role_keywords:
            if word in line.lower():
                roles.append(line.strip())

    for ent in doc.ents:
        if ent.label_ == 'ORG':
            companies.append(ent.text)
        elif ent.label_ == 'DATE':
            durations.append(ent.text)

    return {
        "companies": list(set(companies)),
        "roles": list(set(roles)),
        "durations": list(set(durations))
    }

def extract_list_items(section_text):
    items = []
    lines = section_text.split('\n')
    for line in lines:
        clean_line = re.sub(r'^\s*[-•*]\s*', '', line).strip()
        clean_line = re.sub(r'^\s*\d+[\).\s]\s*', '', clean_line).strip()
        if clean_line:
            items.append(clean_line)
    return items