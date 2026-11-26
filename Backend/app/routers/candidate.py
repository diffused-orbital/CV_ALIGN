from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.application import Application
from app.models.job import Job
from app.models.profile import Profile
from app.routers.auth import get_current_user
from app.utils.storage import upload_pdf, signed_download_url, delete_uploaded_pdf

router = APIRouter(tags=["Candidate"])


def _profile_dict(profile: Profile):
    return {
        "complete": bool(profile and (profile.resume_url or profile.resume_path)),
        "full_name": profile.full_name if profile else None,
        "contact": profile.contact if profile else None,
        "cgpa": profile.cgpa if profile else None,
        "institute": profile.institute if profile else None,
        "degree": profile.degree if profile else None,
        "resume_url": "/candidate/profile/resume" if profile and (profile.resume_url or profile.resume_path) else None,
    }


@router.get("/candidate/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates have a profile.")

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        return {"complete": False}
    return _profile_dict(profile)


@router.post("/candidate/profile")
def save_profile(
    full_name: str = Form(...),
    contact: str = Form(...),
    cgpa: float = Form(...),
    institute: str = Form(...),
    degree: str = Form(...),
    resume: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update the candidate's profile. The resume is uploaded once."""
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can create a profile.")

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()

    # A resume is required to complete a profile for the first time.
    if not profile and resume is None:
        raise HTTPException(status_code=400, detail="A resume (PDF) is required to complete your profile.")

    resume_url = None
    if resume is not None:
        resume_url = upload_pdf(resume, f"cv_align/profiles/{current_user.id}")

    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)

    profile.full_name = full_name
    profile.contact = contact
    profile.cgpa = cgpa
    profile.institute = institute
    profile.degree = degree
    if resume is not None:
        profile.resume_path = resume_url
        profile.resume_url = resume_url

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        if resume_url:
            delete_uploaded_pdf(resume_url)
        raise

    return {"message": "Profile saved successfully!", **_profile_dict(profile)}


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


@router.get("/candidate/profile/resume")
def download_profile_resume(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "candidate":
        raise HTTPException(403, "Only candidates have a profile.")
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile or not profile.resume_url:
        raise HTTPException(404, "No resume is available.")
    try:
        return {"url": signed_download_url(profile.resume_url, attachment=True)}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
