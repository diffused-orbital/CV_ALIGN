# !pip install PyPDF2
# !pip install python-docx
# !pip install langchain_google_genai
# !pip install sentence_transformers


if __name__ == "__main__":
    import requests
    from io import BytesIO
    import fitz 
    import os
    from functions import scoring as sc
    os.environ["GOOGLE_API_KEY"] = "AIzaSyCQwcOs4gYRDS2Iw-_b3DivFcIuVT6zVhw"
    
    cloud_name = "daom8lqfr"
    company_name = "CompanyA"

    # Job Description file
    jd_file_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{company_name}/job_description.pdf"
    jd_response = requests.get(jd_file_url)

    # Resume folder - fetch all files using Cloudinary Admin API
    import cloudinary
    import cloudinary.api

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
    print("\n🏆 Final Ranking 🏆\n")
    for rank, result in enumerate(ranked_results, start=1):
        print(f"Rank {rank}: {result['Name']} - Score: {result['Score']:.2f}/100")
        print("Feedback:")
        print(result["Feedback"])
        print("=" * 50)