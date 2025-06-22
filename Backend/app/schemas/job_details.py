from pydantic import BaseModel
from typing import List, Optional

class CandidateInfo(BaseModel):
    candidate_name: str
    institute: str
    degree: str
    cgpa: float
    score: Optional[float] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    resume_link: str
    status: int

class JobDetail(BaseModel):
    job_id: int
    job_title: str
    company: str
    candidates: List[CandidateInfo]
