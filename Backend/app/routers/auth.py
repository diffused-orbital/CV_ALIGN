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
from app.utils.deps import get_current_user

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
    try:
        print("📥 Incoming user data:", user.dict())
        existing_email = db.query(User).filter(User.email == user.email).first()
        if existing_email:
            print("⚠️ Email already exists:", user.email)
            raise HTTPException(status_code=400, detail="Email already registered")
        
        existing_username = db.query(User).filter(User.username == user.username).first()
        if existing_username:
            print("⚠️ Username already exists:", user.username)
            raise HTTPException(status_code=400, detail="Username already taken")
     
        hashed_pw = pwd_context.hash(user.password)
        new_user = User(username=user.username, email=user.email, hashed_password=hashed_pw, role=user.role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print("✅ Registered new user:", new_user.email)
        return new_user
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 

# @router.post("/login")
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     access_token = create_access_token(
#         data={"sub": user.email, "role": user.role},
#         expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        print(f"🔴 Login failed with error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/secure-data")
def get_secure_data(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}, your role is {current_user.role}!"}


