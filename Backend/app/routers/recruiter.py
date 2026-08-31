import re
import time
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

import cloudinary.utils
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.schemas.job_details import JobDetail, CandidateInfo
from app.routers.application import _persist_scores
from app.config import configure_cloudinary
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


def _cloudinary_asset_reference(url: str) -> tuple[str, None, str]:
    """Extract a raw asset's public ID and delivery type from a Cloudinary URL."""
    path_parts = [unquote(part) for part in urlparse(url).path.split("/") if part]
    try:
        resource_index = path_parts.index("raw")
        delivery_type = path_parts[resource_index + 1]
    except (ValueError, IndexError) as exc:
        raise ValueError("The stored resume is not a valid Cloudinary raw-file URL.") from exc

    asset_parts = path_parts[resource_index + 2:]
    if asset_parts and re.fullmatch(r"v\d+", asset_parts[0]):
        asset_parts = asset_parts[1:]
    if not asset_parts:
        raise ValueError("The stored resume does not include a Cloudinary public ID.")

    filename = PurePosixPath(asset_parts[-1])
    if not filename.suffix:
        raise ValueError("The stored resume does not include a file extension.")
    # Cloudinary raw assets include their extension in the public ID. Passing
    # the ID without it makes the signed download endpoint return 404.
    return "/".join(asset_parts), None, delivery_type


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
        public_id, file_format, delivery_type = _cloudinary_asset_reference(application.resume_path)
        expires_at = int(time.time()) + 300
        configure_cloudinary()
        signed_url = cloudinary.utils.private_download_url(
            public_id,
            file_format,
            resource_type="raw",
            type=delivery_type,
            attachment=True,
            expires_at=expires_at,
        )
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

    safe_company_name = job.company.replace(" ", "_")
    safe_title = job.title.replace(" ", "_")
    try:
        ranked_results = score_cvs_v2(safe_company_name, safe_title)
        _persist_scores(db, job.id, ranked_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}")

    top_applications = (
        db.query(Application)
        .filter(Application.job_id == job.id)
        .order_by(Application.score.desc().nullslast())
        .limit(max(1, top))
        .all()
    )
    candidates = [_candidate_info(db, app) for app in top_applications]

    return {
        "message": f"Scored {len(candidates)} candidate(s).",
        "job_id": job.id,
        "candidates": [c.dict() for c in candidates],
    }
