"""Pydantic schemas for collaborator endpoints."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserSchema(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class CollaboratorSchema(BaseModel):
    name: str
    access_level: str

    class Config:
        from_attributes = True


class CollaboratorAddSchema(BaseModel):
    email: EmailStr
    access_level: Optional[str] = "view"


class CollaboratorResponseSchema(BaseModel):
    name: str
    status: str


class PendingInvitationSchema(BaseModel):

    invited_by: str


    class Config:
        from_attributes = True


class InvitationActionSchema(BaseModel):
    invite_id: int
    action: str  # "accept" or "decline"


class InvitationResponseSchema(BaseModel):
    detail: str