"""Router de autenticación: login (emite token) y me (quién soy)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_token, current_user, hash_password, verify_password
from app.db import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

_HASH_SENUELO = hash_password("timing-attack-decoy")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Verifica email + contraseña y, si son correctos, devuelve un token JWT."""
    user = db.query(User).filter_by(email=data.email).first()
    hash_a_verificar = user.password_hash if user and user.password_hash else _HASH_SENUELO
    password_ok = verify_password(data.password, hash_a_verificar)
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
    """Devuelve los datos del usuario autenticado (según el token del header)."""
    return user
