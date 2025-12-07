import jwt
from django.conf import settings
from datetime import datetime, timedelta
import json


def create_jwt(payload, expires_minutes=1440):
    """Create JWT access token with expiration (default 24 hours)."""
    data = payload.copy()
    exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
    data.update({"exp": exp, "type": "access"})
    token = jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def create_refresh_token(payload, expires_days=7):
    """Create JWT refresh token with longer expiration."""
    data = payload.copy()
    exp = datetime.utcnow() + timedelta(days=expires_days)
    data.update({"exp": exp, "type": "refresh"})
    token = jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_jwt(token):
    """Decode and validate JWT token."""
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return data
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}
    except Exception:
        return None
