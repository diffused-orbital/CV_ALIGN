from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.schemas.job_details import JobDetail, CandidateInfo
from app.routers.application import _persist_scores
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
        resume_link=(app.resume_path or "").replace("\\", "/"),
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

<<<<<<< HEAD
    candidates = []
    for app in applications:
        user = db.query(User).filter(User.id == app.user_id).first()
        candidates.append(CandidateInfo(
            application_id=app.id,
            candidate_name=user.username,
            institute=app.institute,
            degree=app.degree,
            cgpa=app.cgpa,
            score=app.score,
            strengths=app.strengths,
            weaknesses=app.weaknesses,
            resume_link=app.resume_path.replace("\\", "/"),
            status=app.status
        ))
=======
    candidates = [_candidate_info(db, app) for app in applications]
>>>>>>> bcd5ff554286af570b637883b94f730c65ae88b0

    return JobDetail(
        job_id=job.id,
        job_title=job.title,
        company=job.company,
        is_open=bool(job.is_open),
        candidates=candidates,
    )


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
