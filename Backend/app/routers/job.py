from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import Job
from app.models.user import User
from app.models.application import Application
from app.routers.auth import get_current_user
from app.utils.storage import upload_pdf, delete_uploaded_pdf

router = APIRouter()

@router.get("/jobs")
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Any authenticated user can browse jobs. For candidates, annotate each
    # job with whether they have already applied and their application status.
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    my_apps = {
        a.job_id: a
        for a in db.query(Application).filter(Application.user_id == current_user.id).all()
    }
    result = []
    for job in jobs:
        appn = my_apps.get(job.id)
        result.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "is_open": bool(job.is_open),
            "applied": appn is not None,
            "status": appn.status if appn else None,
        })
    return {"jobs": result}

@router.post("/job/upload")
def upload_job_with_pdf(
    title: str = Form(...),
    company: str = Form(...),
    jd_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only recruiters can post jobs
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can post jobs.")

    new_job = Job(title=title, company=company, description_path="pending", posted_by=current_user.id)
    db.add(new_job)
    db.flush()
    cloudinary_jd_url = None
    try:
        cloudinary_jd_url = upload_pdf(jd_file, f"cv_align/jobs/{new_job.id}/jd")
        new_job.description_path = cloudinary_jd_url
        db.commit()
        db.refresh(new_job)
    except Exception:
        db.rollback()
        if cloudinary_jd_url:
            delete_uploaded_pdf(cloudinary_jd_url)
        raise

    return {
        "message": "Job posted successfully!",
        "job_id": new_job.id,
        "cloudinary_url": cloudinary_jd_url
    }
