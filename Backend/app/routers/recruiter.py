import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, lock_job
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.schemas.job_details import JobDetail, CandidateInfo
from app.routers.application import _persist_scores
from app.utils.storage import cloudinary_asset_reference as _cloudinary_asset_reference, signed_download_url
from New_Model.new_main import score_cvs_v2

router = APIRouter(prefix="/recruiter", tags=["Recruiter Dashboard"])


def _owned_job(db: Session, job_id: int, current_user: User) -> Job:
    """Return the job if the current user is the recruiter who posted it."""
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied. Recruiter only.")
    job = db.query(Job).filter(Job.id == job_id, Job.posted_by == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or access denied")
    return job


def _candidate_info(db: Session, app: Application) -> CandidateInfo:
    user = db.query(User).filter(User.id == app.user_id).first()
    return CandidateInfo(
        application_id=app.id,
        candidate_name=user.username if user else "Unknown",
        institute=app.institute,
        degree=app.degree,
        cgpa=app.cgpa,
        score=app.score,
        strengths=app.strengths,
        weaknesses=app.weaknesses,
        status=app.status,
    )


@router.get("/dashboard")
def recruiter_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied. Recruiter only.")

    jobs = db.query(Job).filter(Job.posted_by == current_user.id).all()

    job_summaries = []
    for job in jobs:
        resume_count = db.query(Application).filter(Application.job_id == job.id).count()
        job_summaries.append({
            "job_id": job.id,
            "company": job.company,
            "position": job.title,
            "resumes_applied": resume_count,
            "is_open": bool(job.is_open),
        })

    return {
        "recruiter": current_user.username,
        "total_jobs_posted": len(jobs),
        "jobs": job_summaries
    }


@router.get("/job/{job_id}", response_model=JobDetail)
def get_job_details(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = _owned_job(db, job_id, current_user)

    applications = (
        db.query(Application)
        .filter(Application.job_id == job.id)
        .order_by(Application.score.desc().nullslast())
        .all()
    )

    candidates = [_candidate_info(db, app) for app in applications]

    return JobDetail(
        job_id=job.id,
        job_title=job.title,
        company=job.company,
        is_open=bool(job.is_open),
        candidates=candidates,
    )


@router.get("/application/{application_id}/resume")
def get_resume_download_url(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a short-lived, signed resume URL to the owning recruiter only."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    _owned_job(db, application.job_id, current_user)

    if not application.resume_path or not application.resume_path.startswith(("http://", "https://")):
        raise HTTPException(status_code=404, detail="No Cloudinary resume is available for this application")

    try:
        expires_at = int(time.time()) + 300
        signed_url = signed_download_url(application.resume_path, attachment=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"url": signed_url, "expires_at": expires_at}


@router.post("/job/{job_id}/close")
def close_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Close a job so it stops accepting applications."""
    lock_job(db)
    job = _owned_job(db, job_id, current_user)
    job.is_open = False
    db.commit()
    return {
        "message": "Applications closed. Candidates can no longer apply.",
        "job_id": job.id,
        "is_open": False,
    }


@router.post("/job/{job_id}/generate")
def generate_scores(
    job_id: int,
    top: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run the scoring model over all applications and return the top ranked."""
    job = _owned_job(db, job_id, current_user)
    if job.is_open:
        raise HTTPException(status_code=400, detail="Close the job before generating scores.")

    applications = db.query(Application).filter(Application.job_id == job.id).all()
    if not applications:
        return {"message": "Scored 0 candidate(s).", "job_id": job.id, "scored_count": 0, "candidates": []}
    try:
        ranked_results = score_cvs_v2(
            job.description_path,
            [{"ApplicationId": a.id, "ResumeUrl": a.resume_path} for a in applications],
        )
        scored_count = _persist_scores(db, job.id, ranked_results)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail="Scoring failed. No scores were saved. Check storage and model availability, then retry.") from exc

    top_applications = (
        db.query(Application)
        .filter(Application.job_id == job.id)
        .order_by(Application.score.desc().nullslast())
        .limit(max(1, top))
        .all()
    )
    candidates = [_candidate_info(db, app) for app in top_applications]

    return {
        "message": f"Scored {scored_count} candidate(s).",
        "job_id": job.id,
        "scored_count": scored_count,
        "candidates": [c.model_dump() for c in candidates],
    }
