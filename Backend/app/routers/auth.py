# app/routers/auth.py
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.token import authenticate_user, create_access_token
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from passlib.context import CryptContext
from datetime import timedelta
from app.utils.token import get_current_user

ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = pwd_context.hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pw, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/secure-data")
def get_secure_data(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}, your role is {current_user.role}!"}
