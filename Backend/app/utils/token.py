from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt

from app.models.user import User
from sqlalchemy.orm import Session

from app.config import JWT_SECRET_KEY as SECRET_KEY, JWT_ALGORITHM as ALGORITHM
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password, hashed_password) -> bool:
    if len(plain_password.encode()) > 72:
        return False
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=60)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "purpose": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or payload.get("purpose") != "access":
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception
