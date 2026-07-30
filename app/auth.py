"""Reusable security pieces: password hashing (bcrypt) and JWT tokens (PyJWT)."""

import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import Role
from app.models import User

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing from .env (the secret used to sign the JWT tokens).")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 8


def hash_password(password: str) -> str:
    """Return the bcrypt hash (with a random salt) of a password, ready to store in the database."""
    hash_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check whether a password matches its stored hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(usuario_id: uuid.UUID) -> str:
    """Create a JWT signed with the user id (`sub`) and its expiry (`exp`); the role is not stored."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Verify the token signature and expiry and return its payload; raises jwt.InvalidTokenError if invalid."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


security = HTTPBearer()


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: validates the header token and returns the authenticated user (401 if it fails or is inactive)."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
    )
    try:
        data = decode_token(credentials.credentials)
        usuario_id = uuid.UUID(data["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized from None
    user = db.get(User, usuario_id)
    if user is None or not user.activo:
        raise unauthorized
    return user


def require_role(*allowed_roles: Role):
    """Dependency factory requiring the authenticated user to have one of these roles (403 otherwise)."""

    def check_role(user: User = Depends(current_user)) -> User:
        if user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta acción",
            )
        return user

    return check_role
