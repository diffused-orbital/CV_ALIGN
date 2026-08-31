from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Profile(Base):
    """A candidate's details, entered once and reused for every application."""
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String)
    contact = Column(String)
    cgpa = Column(Float)
    institute = Column(String)
    degree = Column(String)
    resume_path = Column(String)   # local path to the stored resume
    resume_url = Column(String)    # Cloudinary secure URL of the resume

    user = relationship("User", back_populates="profile")
