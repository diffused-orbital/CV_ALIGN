from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.application import Application
from app.models.user import User
from app.models.job import Job
from app.routers.auth import get_current_user
from New_Model.new_main import score_cvs_v2
import shutil
import os
from datetime import datetime

router = APIRouter()

@router.post("/apply")
async def apply_for_job(
    job_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can apply for jobs.")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Save the uploaded resume to the cloud folder structure
    company_folder = job.company.replace(" ", "_")
    resume_dir = f"uploads/{company_folder}/resumes"
    os.makedirs(resume_dir, exist_ok=True)
    file_path = os.path.join(resume_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Simulate Cloudinary path — file should already be uploaded separately in real use
    cloud_resume_path = f"{company_folder}/resumes/{file.filename}"
    jd_path = job.description_path.replace("\\", "/")  # Ensure forward slashes for cloudinary path

    try:
        result = score_cvs_v2(
            cloud_name="daom8lqfr",
            jd_path=jd_path,
            company_name=company_folder
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in model evaluation: {str(e)}")

    # Extract candidate's score and feedback from result
    matched_result = next((r for r in result if r['resume'].endswith(file.filename)), None)
    if not matched_result:
        raise HTTPException(status_code=500, detail="Scoring failed to return result for this resume.")

    score = matched_result['score']
    feedback = matched_result['feedback']

    application = Application(
        job_id=job.id,
        user_id=current_user.id,
        resume_path=cloud_resume_path,
        score=score,
        feedback=feedback,
        created_at=datetime.utcnow(),
        status="pending"
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "message": "Application submitted successfully!",
        "application_id": application.id,
        "score": score,
        "feedback": feedback
    }
