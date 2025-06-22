from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.schemas.job_details import JobDetail, CandidateInfo

router = APIRouter(prefix="/recruiter", tags=["Recruiter Dashboard"])


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
            "resumes_applied": resume_count
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
    job = db.query(Job).filter(Job.id == job_id, Job.posted_by == current_user.id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found or access denied")

    applications = (
        db.query(Application)
        .filter(Application.job_id == job.id)
        .order_by(Application.score.desc().nullslast())
        .all()
    )

    candidates = []
    for app in applications:
        user = db.query(User).filter(User.id == app.user_id).first()
        candidates.append(CandidateInfo(
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

    return JobDetail(
        job_id=job.id,
        job_title=job.title,
        company=job.company,
        candidates=candidates
    )
