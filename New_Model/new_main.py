def score_cvs_v2(job_description_url, applications):
    """Score exactly the application's database records, including older assets."""
    from app.utils.storage import signed_download_url
    from .functions.scoring import process_resumes

    # Sign each resume immediately before processing it, so links for later
    # applicants do not expire while earlier model calls are running.
    resumes = (
        {"ApplicationId": application["ApplicationId"], "ResumeUrl": signed_download_url(application["ResumeUrl"])}
        for application in applications
    )
    return process_resumes(resumes, signed_download_url(job_description_url))
