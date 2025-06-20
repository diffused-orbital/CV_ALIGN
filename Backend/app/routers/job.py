from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import Job
from app.models.user import User
from app.routers.auth import get_current_user
from datetime import datetime
import os
import shutil

router = APIRouter()

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

    # Save PDF locally (replace this with cloud upload later)
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_location = os.path.join(upload_dir, jd_file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(jd_file.file, buffer)

    # Save job in DB
    new_job = Job(
        title=title,
        company=company,
        description_path=file_location,
        posted_by=current_user.id,
        created_at=datetime.utcnow()
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return {
        "message": "Job posted successfully!",
        "job_id": new_job.id,
        "file_path": file_location
    }
