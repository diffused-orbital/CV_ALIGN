from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Application, Job
from app.routers.auth import get_current_user
from app.schemas.user import UserOut

router = APIRouter()

status_map = {
    0: "pending",
    1: "accepted",
    2: "rejected"
}

@router.get("/dashboard/candidate")
def candidate_dashboard(
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can access this route.")

    applications = db.query(Application).filter(Application.user_id == current_user.id).all()
    result = []

    for app in applications:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if job:
            result.append({
                "job_title": job.title,
                "company": job.company,
                "status": status_map.get(app.status, "unknown")
            })

    return {"applications": result}
