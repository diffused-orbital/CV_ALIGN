from sqlalchemy import Column, ForeignKey, Integer, String

from app.database import Base


class PasswordReset(Base):
    __tablename__ = "password_resets"

    token_hash = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(Integer, nullable=False)


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"

    key = Column(String, primary_key=True)
    window = Column(Integer, nullable=False)
    count = Column(Integer, nullable=False)
