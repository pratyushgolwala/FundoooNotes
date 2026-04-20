import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings


def generate_bearer_token(user_id: int, hours: int = 1) -> str:
    """Generate a short-lived bearer token (1 hour by default)."""
    payload = {
        "user_id": user_id,
        "token_type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=hours),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def generate_refresh_token(user_id: int, days: int = 7) -> str:
    """Generate a long-lived refresh token (7 days by default)."""
    payload = {
        "user_id": user_id,
        "token_type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=days),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def generate_tokens(user_id: int) -> dict:
    """Generate both bearer and refresh tokens."""
    bearer_token = generate_bearer_token(user_id)
    refresh_token = generate_refresh_token(user_id)
    return {
        "access_token": bearer_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": 3600,  # 1 hour in seconds
    }


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
