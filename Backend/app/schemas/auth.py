from pydantic import BaseModel

# Used when logging in
class UserLogin(BaseModel):
    username: str
    password: str

# Returned when login is successful
class Token(BaseModel):
    access_token: str
    token_type: str
