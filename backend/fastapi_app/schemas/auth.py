"""Authentication schemas for login endpoints."""
from pydantic import BaseModel, EmailStr


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    user_email: str
    user_name: str