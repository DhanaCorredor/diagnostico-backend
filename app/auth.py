"""Piezas de seguridad reutilizables: hash de contraseñas (bcrypt) y tokens JWT (PyJWT)."""

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
from app.enums import Rol
from app.models import Usuario

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("Falta JWT_SECRET en el .env (secreto para firmar los tokens JWT).")
JWT_ALGORITHM = "HS256"
JWT_EXPIRA_MINUTOS = 60 * 8


def hashear_password(password: str) -> str:
    """Devuelve el hash bcrypt (con sal aleatoria) de una contraseña, listo para guardar en la BD."""
    hash_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    """Comprueba si una contraseña coincide con su hash guardado."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def crear_token(usuario_id: uuid.UUID) -> str:
    """Crea un JWT firmado con el id del usuario (`sub`) y su caducidad (`exp`); el rol no se guarda."""
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "exp": ahora + timedelta(minutes=JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Verifica firma y caducidad del token y devuelve su payload; lanza jwt.InvalidTokenError si no es válido."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


security = HTTPBearer()


def usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia: valida el token del header y devuelve el usuario autenticado (401 si falla o está inactivo)."""
    no_autorizado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
    )
    try:
        datos = decodificar_token(credentials.credentials)
        usuario_id = uuid.UUID(datos["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise no_autorizado from None
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise no_autorizado
    return usuario


def requiere_rol(*roles_permitidos: Rol):
    """Fábrica de dependencias que exige que el usuario autenticado tenga uno de estos roles (403 si no)."""

    def verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta acción",
            )
        return usuario

    return verificar
