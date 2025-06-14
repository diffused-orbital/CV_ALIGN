import re


def extract_job_section(text, section_names, all_section_names):
    # Create regex pattern for target section names
    section_pattern = r'|'.join([re.escape(name) for name in section_names])

    # Find the start of the target section
    start_match = re.search(rf'({section_pattern})[:\s]*', text, re.I)
    if not start_match:
        return ""

    start_index = start_match.end()

    # Extract the remaining text to analyze for end boundary
    remaining_text = text[start_index:]

    # Create a list of lowercased section headers sorted by length (longest first for accurate phrase matching)
    all_section_names_sorted = sorted(all_section_names, key=len, reverse=True)

    # Build regex pattern for detecting section boundaries in the text (phrase-aware!)
    boundary_pattern = r'|'.join([re.escape(name) for name in all_section_names_sorted])
    boundary_regex = re.compile(boundary_pattern, re.I)

    # Scan the remaining text for the next section boundary
    match = boundary_regex.search(remaining_text)
    if match:
        # Found a next section header candidate
        next_section = match.group(0).strip().lower()
        if next_section not in section_names:
            # It's a valid new section - stop here
            end_index = start_index + match.start()
        else:
            # It's a repetition of the current section - continue
            end_index = len(text)
    else:
        # No next section found - take till the end
        end_index = len(text)

    section_text = text[start_index:end_index].strip()

    # Clean up: remove bullet points, extra spaces, newlines
    section_text = re.sub(r'[\u2022•▪️]', '', section_text)  # Remove common bullet characters
    section_text = re.sub(r'\n+', '\n', section_text)
    section_text = re.sub(r'\s+', ' ', section_text)

    return section_text.strip()

ALL_JOB_SECTION_NAMES = [
    'job summary', 'summary', 'job description', 'description',
    'key responsibilities', 'responsibilities', 'roles and responsibilities',
    'required skills', 'required qualifications', 'required experience', 'requirements',
    'preferred skills', 'preferred qualifications', 'preferred experience', 'nice to have',
]


def extract_job_summary(text):
    section_names = ['job summary', 'summary', 'job description', 'description']
    return extract_job_section(text, section_names, ALL_JOB_SECTION_NAMES)

def extract_key_responsibilities(text):
    section_names = ['key responsibilities', 'responsibilities', 'roles and responsibilities']
    return extract_job_section(text, section_names, ALL_JOB_SECTION_NAMES)

def extract_required_skills(text):
    section_names = ['required skills', 'required qualifications', 'required experience', 'requirements']
    return extract_job_section(text, section_names, ALL_JOB_SECTION_NAMES)

def extract_preferred_skills(text):
    section_names = ['preferred skills', 'preferred qualifications', 'preferred experience', 'nice to have']
    return extract_job_section(text, section_names, ALL_JOB_SECTION_NAMES)

# def extract_experience(text):
#     section_names = ['experience']
#     return extract_job_section(text, section_names, ALL_JOB_SECTION_NAMES)

# def extract_qualifications(text):
#     section_names = ['qualifications']
#     return extract_job_section(text, section_names, ALL_JOB_SECTION_NAMES)

# def extract_skills(text):
#     section_names = ['skills']
#     return extract_job_section(text, section_names, ALL_JOB_SECTION_NAMES)

def extract_job_details(full_text):
    # Extract sections
    summary_text = extract_job_summary(full_text)
    responsibilities_text = extract_key_responsibilities(full_text)
    required_skills_text = extract_required_skills(full_text)
    preferred_skills_text = extract_preferred_skills(full_text)

    # Final dictionary
    return {
        "summary": summary_text,
        "responsibilities": responsibilities_text,
        "required_skills": required_skills_text,
        "preferred_skills": preferred_skills_text
    }
