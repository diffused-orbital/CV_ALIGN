# !pip install PyPDF2
# !pip install python-docx
# !pip install langchain_google_genai
# !pip install sentence_transformers

def score_cvs_v2(company_name,role_name):
    import requests
    from io import BytesIO
    import fitz
    import os
    from .functions import scoring as sc
    import sys
    import cloudinary
    import cloudinary.api
    from dotenv import load_dotenv

    # Load credentials from the environment (.env). GOOGLE_API_KEY is read
    # from the environment by LangChain; Cloudinary is configured from env too.
    load_dotenv()

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )

    base_prefix = f"{company_name}/{role_name}"

    jd_files = cloudinary.api.resources(
        resource_type="raw",
        type="upload",
        prefix=f"{base_prefix}/job_description"
    )["resources"]

    if not jd_files:
        raise FileNotFoundError(f"No JD file found in {base_prefix}")

    jd_file_url = jd_files[0]["secure_url"]

    # Resume folder - fetch all files using Cloudinary Admin API
    resume_urls = []
    result = cloudinary.api.resources(
        resource_type='raw',
        type='upload',
        prefix=f'{base_prefix}/resumes/',
    )
    for resource in result.get('resources',[]):
        resume_urls.append(resource['secure_url'])

    if not resume_urls:
        raise FileNotFoundError(f"No resumes found in {base_prefix}/resumes")

    ranked_results = sc.process_resumes(resume_urls, jd_file_url)
    # ranked_results = [{"Name", "Score", "Feedback"}, ...]
    return ranked_results
