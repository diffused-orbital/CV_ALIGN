from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.job import JobCreate, JobOut
from app.models.job import Job
from app.utils.token import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/job/", response_model=JobOut)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can create jobs.")
    
    new_job = Job(
        title=job.title,
        company=job.company,
        description_path=job.description_path,  
        posted_by=current_user.id              
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


