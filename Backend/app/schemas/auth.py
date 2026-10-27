from pydantic import BaseModel, EmailStr

# Used when logging in
class UserLogin(BaseModel):
    username: str
    password: str

# Returned when login is successful
class Token(BaseModel):
    access_token: str
    token_type: str

# Password reset
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
