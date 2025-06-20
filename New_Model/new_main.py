# new_main.py

from New_Model.functions import scoring as sc
import requests
import os
import cloudinary
import cloudinary.api

def score_cvs_v2(cloud_name: str,jd_path: str, company_name: str):
    os.environ["GOOGLE_API_KEY"] = "AIzaSyCQwcOs4gYRDS2Iw-_b3DivFcIuVT6zVhw"

    # Job Description file
    jd_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{jd_path.replace('\\', '/')}"
    jd_response = requests.get(jd_url)

    # Resume folder - fetch all files using Cloudinary Admin API
    cloudinary.config(
        cloud_name=cloud_name,
        api_key='833671224989892',
        api_secret='GhNtyL1tRnTOWchvUSlJqsFUExU',
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

    ranked_results = sc.process_resumes(resume_urls, jd_response)
    return ranked_results
