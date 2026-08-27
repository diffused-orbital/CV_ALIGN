from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.routers.auth import get_current_user
from New_Model.new_main import score_cvs_v2
import shutil
import os
import re
import uuid
from pathlib import Path as FilePath
import cloudinary
import cloudinary.uploader

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
    by_stem = {FilePath(a.resume_path).stem: a for a in applications}

    for result in ranked_results or []:
        application = by_stem.get(result.get("Name"))
        if not application:
            continue
        application.score = result.get("Score")
        strengths, weaknesses = _split_feedback(result.get("Feedback"))
        application.strengths = strengths
        application.weaknesses = weaknesses

    db.commit()

cloudinary.config(
    cloud_name="daom8lqfr",
    api_key='833671224989892',
    api_secret='GhNtyL1tRnTOWchvUSlJqsFUExU',
    secure=True
)

@router.post("/apply")
def apply_to_job(
    job_id: int = Form(...),
    cgpa: float = Form(...),
    institute: str = Form(...),
    degree: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only candidates can apply to jobs
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can apply to jobs.")

    # Check if job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Prevent duplicate applications
    existing = db.query(Application).filter(
        Application.job_id == job.id,
        Application.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this job.")

    # Validate file format
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF resumes are allowed.")

    company_name = job.company
    title = job.title
    safe_company_name = company_name.replace(" ", "_")
    safe_title = title.replace(" ", "_")

    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    upload_dir = f"uploads/{safe_company_name}/{safe_title}/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    # Save file locally
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload to Cloudinary
    cloudinary_path = f"{safe_company_name}/{safe_title}/resumes/{filename}"
    try:
        cloudinary.uploader.upload(
            file_path,
            resource_type="raw",
            public_id=cloudinary_path,
            overwrite=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {e}")

    # Insert application in DB
    application = Application(
        job_id=job.id,
        user_id=current_user.id,
        resume_path=file_path.replace("\\", "/"),
        status=0,
        cgpa=cgpa,
        institute=institute,
        degree=degree
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Trigger scoring for all resumes under this job and persist the results
    try:
        ranked_results = score_cvs_v2(safe_company_name, safe_title)
        _persist_scores(db, job.id, ranked_results)
    except Exception as e:
        print(f"⚠️ Scoring model failed: {e}")

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
