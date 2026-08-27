from fastapi import FastAPI, Depends
import os
import sys
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

# Windows consoles default to cp1252, which can't encode the emoji used in
# debug prints; that would raise UnicodeEncodeError and 500 the request.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
from .database import Base, engine
from .models import user
from app.routers import auth
from app.utils.deps import get_current_user
from app.models.user import User

from app.database import create_tables
create_tables()

Base.metadata.create_all(bind=engine)

# Make the repo root importable so routers can `import New_Model.*`
sys.path.append(str(Path(__file__).resolve().parents[2]))


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Backend is up and running!"}

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

from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])