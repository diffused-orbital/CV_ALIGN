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
import uuid
import cloudinary
import cloudinary.uploader

router = APIRouter(tags=["Applications"])

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

    # Trigger scoring
    try:
        score_cvs_v2(safe_company_name, safe_title)
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

    application.status = -1  # Rejected
    db.commit()
    return {"message": "Application rejected successfully", "application_id": application_id}
