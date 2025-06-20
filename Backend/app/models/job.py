from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description_path = Column(String, nullable=False)  
    company = Column(String, nullable=False)
    posted_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    recruiter = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job")


# class Application(Base):
#     __tablename__ = "applications"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     job_id = Column(Integer, ForeignKey("jobs.id"))
#     resume_path = Column(String, nullable=False)
#     score = Column(Float)
#     feedback = Column(Text)
#     status = Column(String, default="Pending")  # "Pending", "Accepted", "Rejected"
#     applied_at = Column(DateTime, default=datetime.utcnow)

#     candidate = relationship("User", back_populates="applications")
#     job = relationship("Job", back_populates="applications")
