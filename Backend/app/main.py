from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import os
import sys 
import shutil
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from Model.pipeline import score_cvs  # Adjusted import from Model directory

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Backend is up and running!"}

@app.post("/score/")
async def score_resumes(
    job_desc: UploadFile = File(...),
    cvs: List[UploadFile] = File(...)
):
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

    # Run the scoring function
    try:
        results = score_cvs(job_desc_path, cv_paths, top_k=5)
        return JSONResponse(content={"results": results})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
