"""Authentication router: login (issues a token) and me (who am I)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_token, current_user, hash_password, verify_password
from app.db import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserOut
from app.services.common import normalized

router = APIRouter(prefix="/auth", tags=["auth"])

_DECOY_HASH = hash_password("timing-attack-decoy")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Check email + password and, if they are correct, return a JWT token.

    The email is matched ignoring case, the same way duplicates are rejected when creating users.
    """
    user = db.query(User).filter(normalized(User.email) == normalized(data.email)).first()
    hash_to_verify = user.password_hash if user and user.password_hash else _DECOY_HASH
    password_ok = verify_password(data.password, hash_to_verify)
    if user is None or not user.password_hash or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )
    token = create_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)):
    """Return the data of the authenticated user (according to the header token)."""
    return user
