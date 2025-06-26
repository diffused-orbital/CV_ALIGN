from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.application import Application
from app.models.job import Job
from app.routers.auth import get_current_user

router = APIRouter(tags=["Candidate"])

@router.get("/candidate/dashboard")
def candidate_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can view this dashboard.")

    applications = db.query(Application).filter(Application.user_id == current_user.id).all()

    dashboard_data = []
    for app in applications:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if not job:
            continue

        dashboard_data.append({
            "job_title": job.title,
            "company": job.company,
            "status": (
                "Pending" if app.status == 0 else
                "Accepted" if app.status == 1 else
                "Rejected"
            )
        })

    return {
        "candidate": current_user.username,
        "applications": dashboard_data
    }
