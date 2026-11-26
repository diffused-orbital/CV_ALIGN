# app/routers/auth.py
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.token import authenticate_user, create_access_token, hash_password
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import secrets
import time
from sqlalchemy import delete, update
from app import config
from app.models.password_reset import PasswordReset
from app.utils.password_reset import check_rate_limit, token_hash, send_reset_email
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from datetime import timedelta
from app.utils.deps import get_current_user

ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES
RESET_TOKEN_EXPIRE_MINUTES = 15

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        if not 6 <= len(user.password.encode()) <= 72:
            raise HTTPException(400, "Password must be 6 to 72 bytes long.")
        existing_email = db.query(User).filter(User.email == user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        existing_username = db.query(User).filter(User.username == user.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")
     
        hashed_pw = hash_password(user.password)
        new_user = User(username=user.username, email=user.email, hashed_password=hashed_pw, role=user.role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except HTTPException:
        # Preserve intentional 4xx responses (e.g. duplicate email/username)
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(
            data={"sub": user.email, "role": user.role, "auth_version": user.auth_version},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        # Preserve intentional 401 for invalid credentials
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not config.SMTP_HOST or not config.SMTP_FROM:
        raise HTTPException(503, "Password-reset email is unavailable. Please contact support.")
    check_rate_limit(db, f"forgot-ip:{request.client.host}", 20)
    check_rate_limit(db, f"forgot-email:{payload.email.lower()}", 5)
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        token = secrets.token_urlsafe(32)
        digest = token_hash(token)
        db.execute(delete(PasswordReset).where(PasswordReset.user_id == user.id))
        db.add(PasswordReset(token_hash=digest, user_id=user.id, expires_at=int(time.time()) + RESET_TOKEN_EXPIRE_MINUTES * 60))
        db.commit()
        background_tasks.add_task(send_reset_email, user.email, token, digest)
    return {"message": "If an account exists, a password-reset link has been sent to its email address."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(db, f"reset-ip:{request.client.host}", 20)
    if not 6 <= len(payload.new_password) <= 72 or len(payload.new_password.encode()) > 72:
        raise HTTPException(400, "Password must be 6 to 72 bytes long.")
    # DELETE RETURNING consumes the token atomically even with concurrent requests.
    user_id = db.execute(
        delete(PasswordReset).where(
            PasswordReset.token_hash == token_hash(payload.token),
            PasswordReset.expires_at > int(time.time()),
        ).returning(PasswordReset.user_id)
    ).scalar_one_or_none()
    if user_id is None:
        db.rollback()
        raise HTTPException(400, "Invalid or expired reset token.")
    db.execute(update(User).where(User.id == user_id).values(
        hashed_password=hash_password(payload.new_password),
        auth_version=User.auth_version + 1,
    ))
    db.execute(delete(PasswordReset).where(PasswordReset.user_id == user_id))
    db.commit()
    return {"message": "Password reset successful. You can now log in."}


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/secure-data")
def get_secure_data(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}, your role is {current_user.role}!"}


