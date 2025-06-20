from pydantic import BaseModel
from typing import Optional

class ApplicationCreate(BaseModel):
    job_id: int

class ApplicationOut(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    score: Optional[float]
    feedback: Optional[str]
    status: str

    class Config:
        orm_mode = True
