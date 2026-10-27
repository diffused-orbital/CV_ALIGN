from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.profile import Profile
from app.routers.auth import get_current_user
from app.schemas.application import ApplicationCreate
import re
import uuid
from pathlib import Path as FilePath
import cloudinary
import cloudinary.uploader
from app.config import configure_cloudinary

router = APIRouter(tags=["Applications"])


def _split_feedback(feedback: str):
    """Split the LLM feedback string into (strengths, weaknesses)."""
    if not feedback:
        return None, None
    match = re.search(r"(?is)strengths\s*:?(.*?)weaknesses\s*:?(.*)", feedback)
    if match:
        strengths = match.group(1).strip()
        weaknesses = match.group(2).strip()
        return strengths or None, weaknesses or None
    return feedback.strip() or None, None


def _authorize_status_change(db: Session, application: Application, current_user: User):
    """Only the recruiter who posted the job may change an application's status."""
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can update application status.")

    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job or job.posted_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only manage applications for your own jobs.")


def _persist_scores(db: Session, job_id: int, ranked_results):
    """Map ranked model results back onto Application rows and save them.

    The model keys each result by the resume filename stem (a UUID for
    uploads), which matches the stem of Application.resume_path.
    """
    applications = db.query(Application).filter(Application.job_id == job_id).all()
    by_stem = {FilePath((a.resume_path or "").split("?")[0]).stem: a for a in applications}

    for result in ranked_results or []:
        application = by_stem.get(result.get("Name"))
        if not application:
            continue
        application.score = result.get("Score")
        strengths, weaknesses = _split_feedback(result.get("Feedback"))
        application.strengths = strengths
        application.weaknesses = weaknesses

    db.commit()

configure_cloudinary()

@router.post("/apply")
def apply_to_job(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """One-click apply using the candidate's saved profile and resume.

    Scoring is not run here; the recruiter triggers it from the job page
    after closing the job (see /recruiter/job/{id}/generate).
    """
    # Only candidates can apply to jobs
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can apply to jobs.")

    # Check if job exists and is still accepting applications
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.is_open:
        raise HTTPException(status_code=400, detail="This job is no longer accepting applications.")

    # Require a completed profile (with a resume) before applying
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile or not profile.resume_path:
        raise HTTPException(
            status_code=400,
            detail="Complete your profile (including a resume) before applying.",
        )

    # Prevent duplicate applications
    existing = db.query(Application).filter(
        Application.job_id == job.id,
        Application.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this job.")

    safe_company_name = job.company.replace(" ", "_")
    safe_title = job.title.replace(" ", "_")

    # Copy the profile resume into this job's Cloudinary folder so scoring
    # (which lists resumes by prefix) can find it. The UUID filename stem is
    # the join key used when persisting scores back onto the application.
    filename = f"{uuid.uuid4()}.pdf"
    cloudinary_path = f"{safe_company_name}/{safe_title}/resumes/{filename}"
    # Prefer the local file; fall back to the stored Cloudinary URL if it is gone.
    source = profile.resume_path
    if not (source and FilePath(source).exists()):
        source = profile.resume_url
    configure_cloudinary()
    try:
        result = cloudinary.uploader.upload(
            source,
            resource_type="raw",
            public_id=cloudinary_path,
            overwrite=True,
        )
        resume_url = result["secure_url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {e}")

    # Insert application in DB, copying details from the profile
    application = Application(
        job_id=job.id,
        user_id=current_user.id,
        resume_path=resume_url,
        status=0,
        cgpa=profile.cgpa,
        institute=profile.institute,
        degree=profile.degree
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "message": "Application submitted successfully!",
        "application_id": application.id
    }

@router.post("/application/{application_id}/accept")
def accept_application(
    application_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    _authorize_status_change(db, application, current_user)

    application.status = 1  # Accepted
    db.commit()
    return {"message": "Application accepted successfully", "application_id": application_id}

@router.post("/application/{application_id}/reject")
def reject_application(
    application_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    _authorize_status_change(db, application, current_user)

    application.status = 2  # Rejected
    db.commit()
    return {"message": "Application rejected successfully", "application_id": application_id}
