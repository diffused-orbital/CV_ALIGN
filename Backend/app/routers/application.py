from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app.database import get_db, lock_job
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.profile import Profile
from app.routers.auth import get_current_user
from app.schemas.application import ApplicationCreate
import re
from pathlib import Path as FilePath
from app.utils.storage import download_pdf, upload_pdf_bytes, delete_uploaded_pdf
from sqlalchemy.exc import IntegrityError

router = APIRouter(tags=["Applications"])


def _split_feedback(feedback: str):
    """Split the LLM feedback string into (strengths, weaknesses)."""
    if not feedback:
        return None, None
    feedback = re.sub(r"\*{1,2}", "", feedback)
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
    """Validate a complete scoring batch and persist it atomically by application ID.

    Filename matching remains supported for older model integrations.
    """
    applications = db.query(Application).filter(Application.job_id == job_id).all()
    by_id = {a.id: a for a in applications}
    by_stem = {FilePath((a.resume_path or "").split("?")[0]).stem: a for a in applications}
    seen = set()
    updates = []
    for result in ranked_results or []:
        application = by_id.get(result.get("ApplicationId")) if "ApplicationId" in result else by_stem.get(result.get("Name"))
        if application is None or application.id in seen:
            raise ValueError("Scoring returned an unknown or repeated application.")
        score = float(result["Score"])
        if not 0 <= score <= 100:
            raise ValueError("Scores must be finite numbers between 0 and 100.")
        seen.add(application.id)
        updates.append((application, score, _split_feedback(result.get("Feedback"))))
    if seen != set(by_id):
        raise ValueError("Scoring did not return a result for every application.")
    for application, score, (strengths, weaknesses) in updates:
        application.score = score
        application.strengths = strengths
        application.weaknesses = weaknesses
    db.commit()
    return len(updates)


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

    lock_job(db)

    # Check if job exists and is still accepting applications
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.is_open:
        raise HTTPException(status_code=400, detail="This job is no longer accepting applications.")

    # Require a completed profile (with a resume) before applying
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile or not (profile.resume_url or profile.resume_path):
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

    source = profile.resume_url or profile.resume_path
    content = download_pdf(source)
    resume_url = upload_pdf_bytes(content, f"cv_align/jobs/{job.id}/resumes")

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
    try:
        db.add(application)
        db.commit()
        db.refresh(application)
    except IntegrityError as exc:
        db.rollback()
        delete_uploaded_pdf(resume_url)
        raise HTTPException(400, "You have already applied to this job.") from exc
    except Exception:
        db.rollback()
        delete_uploaded_pdf(resume_url)
        raise

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
    return {"message": "Application accepted successfully", "application_id": application_id, "status": application.status}

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
    return {"message": "Application rejected successfully", "application_id": application_id, "status": application.status}


@router.post("/application/{application_id}/revert")
def revert_application(
    application_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    _authorize_status_change(db, application, current_user)

    application.status = 0  # Pending
    db.commit()
    return {"message": "Application reverted to pending", "application_id": application_id, "status": application.status}
