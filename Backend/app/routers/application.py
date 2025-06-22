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
import cloudinary.uploader
from New_Model.new_main import score_cvs_v2  

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
    safe_company_name = job.company.replace(" ", "_")
    upload_dir = f"uploads/{safe_company_name}/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    # Save file locally
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload file to Cloudinary
    cloudinary_path = f"{safe_company_name}/resumes/{filename}"
    cloudinary.uploader.upload(
        file_path,
        resource_type="raw",
        public_id=cloudinary_path,
        overwrite=True
    )

    # Insert application into DB
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

    # Trigger model
    jd_file_url = f"https://res.cloudinary.com/daom8lqfr/raw/upload/{safe_company_name}/job_description.pdf"
    try:
        score_cvs_v2(jd_file_url, safe_company_name)
    except Exception as e:
        print(f"⚠️ Scoring model failed: {e}")

    return {
        "message": "Application submitted successfully!",
        "application_id": application.id
    }
