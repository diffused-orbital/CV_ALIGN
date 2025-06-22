from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import sys 
import shutil
from pathlib import Path

from .database import Base, engine
from .models import user  
from app.routers import auth
from app.utils.deps import get_current_user
from app.models.user import User
from fastapi import Depends

from app.database import create_tables
create_tables()

Base.metadata.create_all(bind=engine)


sys.path.append(str(Path(__file__).resolve().parents[2]))


from New_Model.new_main import score_cvs_v2


app = FastAPI()
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Backend is up and running!"}

@app.post("/score/")
async def score_resumes(
    job_desc: UploadFile = File(...),
    cvs: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied: Recruiters only")
    # Save job description
    job_desc_path = os.path.join(UPLOAD_DIR, job_desc.filename)
    with open(job_desc_path, "wb") as f:
        shutil.copyfileobj(job_desc.file, f)

    # Save CVs
    cv_paths = []
    for cv in cvs:
        cv_path = os.path.join(UPLOAD_DIR, cv.filename)
        with open(cv_path, "wb") as f:
            shutil.copyfileobj(cv.file, f)
        cv_paths.append(cv_path)

    # Run the new scoring function
    try:
        results = score_cvs_v2(job_desc_path, cv_paths, top_k=5)
        return JSONResponse(content={"results": results})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/cloud_score/")
async def cloud_score(
    company_name: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied: Recruiters only")
    
    try:
        cloud_name = "daom8lqfr" 
        results = score_cvs_v2(cloud_name, company_name)
        return JSONResponse(content={"results": results})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/upload_cv/")
async def upload_cv(company_name: str = Form(...), file: UploadFile = File(...)):
    # Just log for now
    print(f"Resume received for {company_name}: {file.filename}")
    return {"status": "ok", "company": company_name, "filename": file.filename}

@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }

@app.get("/secure-data")
def get_secure_data(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}, your role is {current_user.role}!"}

from app.routers import job  
app.include_router(job.router, tags=["Job Management"])  

from app.routers import application
app.include_router(application.router)

from app.routers import candidate
app.include_router(candidate.router)

from app.routers import recruiter
app.include_router(recruiter.router)

