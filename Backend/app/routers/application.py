from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.routers.auth import get_current_user
import shutil
import os
import uuid

router = APIRouter(tags=["Applications"])

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
    # Check if job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Generate a unique filename
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    upload_dir = f"uploads/{job.company}/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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

    return {
        "message": "Application submitted successfully!",
        "application_id": application.id
    }
