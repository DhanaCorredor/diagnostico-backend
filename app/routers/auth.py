"""Router de autenticación: login (emite token) y me (quién soy)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import crear_token, usuario_actual, verificar_password
from app.db import get_db
from app.models import Usuario
from app.schemas import LoginRequest, TokenResponse, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    """Verifica email + contraseña y, si son correctos, devuelve un token JWT."""
    usuario = db.query(Usuario).filter_by(email=datos.email).first()
    # Mismo mensaje para 'no existe' y 'contraseña mala': no revelamos cuál falló.
    if (
        usuario is None
        or not usuario.password_hash
        or not verificar_password(datos.password, usuario.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )
    token = crear_token(usuario.id, usuario.rol.value)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(usuario_actual)):
    """Devuelve los datos del usuario autenticado (según el token del header)."""
    return usuario
