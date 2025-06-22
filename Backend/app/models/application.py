from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    resume_path = Column(String)
    score = Column(Float)
    strengths = Column(Text)
    weaknesses = Column(Text)
    status = Column(Integer, default=0)  # 0 = pending, 1 = accepted, 2 = rejected
    cgpa = Column(Float)
    institute = Column(String)
    degree = Column(String)

    # Relationships
    candidate = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
