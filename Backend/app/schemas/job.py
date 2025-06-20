from pydantic import BaseModel

# class JobCreate(BaseModel):
#     title: str
#     company: str
#     description_path: str  

class JobOut(BaseModel):
    id: int
    title: str
    company: str
    description_path: str  
    posted_by: int         

    class Config:
        orm_mode = True

