from pydantic import BaseModel
from typing import List

class JobSummary(BaseModel):
    job_id: int
    company: str
    title: str
    resumes_applied: int

class RecruiterDashboard(BaseModel):
    recruiter_name: str
    total_jobs_posted: int
    jobs: List[JobSummary]
