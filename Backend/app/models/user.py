from sqlalchemy import Column, Integer, String
from ..database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # "recruiter", "candidate", "admin"
    jobs = relationship("Job", back_populates="recruiter")  # for recruiters
    applications = relationship("Application", back_populates="candidate")  # for candidates
