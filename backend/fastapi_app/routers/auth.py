"""Authentication router for FastAPI - handles login."""
from fastapi import APIRouter, HTTPException, status
from django.contrib.auth.hashers import check_password

from users.models import User
from users.token_utils import generate_tokens

from ..schemas.auth import LoginSchema, TokenResponseSchema
from ..schemas.common import ApiResponseSchema
from common.api_response import build_api_response

router = APIRouter(prefix="/fastapi", tags=["auth"])


@router.post("/login/", response_model=ApiResponseSchema)
def login(credentials: LoginSchema):
    """Authenticate user and return JWT tokens."""
    email = credentials.email
    password = credentials.password
    
    # Get user from database
    user = User.objects.filter(email=email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not check_password(password, user.password):  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT tokens
    tokens = generate_tokens(user.id)  # type: ignore[attr-defined]
    
    payload = TokenResponseSchema(
        access_token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        token_type=tokens['token_type'],
        user_id=user.id,  # type: ignore[attr-defined]
        user_email=user.email,
        user_name=user.name,
    )
    return build_api_response("Login successful", payload.dict(), status.HTTP_200_OK)