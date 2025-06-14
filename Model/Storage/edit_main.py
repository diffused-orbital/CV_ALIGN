if __name__ == "__main__":
    import requests
    from io import BytesIO
    import fitz  # PyMuPDF, used to extract text from PDFs

    cloud_name = "your_cloud_name"
    company_name = "CompanyA"

    # Job Description file
    jd_file_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{company_name}/job_description.pdf"
    jd_response = requests.get(jd_file_url)
    jd_text = fitz.open("pdf", BytesIO(jd_response.content))

    # Resume folder - fetch all files using Cloudinary Admin API
    import cloudinary
    import cloudinary.api

    cloudinary.config(
        cloud_name=cloud_name,
        api_key='your_api_key',
        api_secret='your_api_secret',
        secure=True
    )

    resume_urls = []
    result = cloudinary.api.resources(
        type='upload',
        prefix=f'{company_name}/resumes/',
        resource_type='raw'
    )

    for resource in result['resources']:
        resume_urls.append(resource['secure_url'])

    # Load and process resumes
    ranked_results = process_resumes_from_urls(resume_urls, jd_text)

def process_resumes_from_urls(resume_urls, jd_text):
    import fitz

    scores = []
    for url in resume_urls:
        response = requests.get(url)
        pdf = fitz.open("pdf", BytesIO(response.content))
        resume_text = "".join([page.get_text() for page in pdf])

        # Example similarity function
        score = calculate_similarity(resume_text, jd_text)
        scores.append((url, score))

    return sorted(scores, key=lambda x: x[1], reverse=True)
