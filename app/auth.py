"""Piezas de seguridad: hash de contraseñas (bcrypt) y tokens JWT (PyJWT).

Son funciones reutilizables, sin endpoints. Los routers de la Fase 2 las usan
para el login y para verificar el token en cada petición.
"""

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
from app.models import Rol, Usuario

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("Falta JWT_SECRET en el .env (secreto para firmar los tokens JWT).")
JWT_ALGORITHM = "HS256"
JWT_EXPIRA_MINUTOS = 60 * 8


def hashear_password(password: str) -> str:
    """Convierte una contraseña en un hash seguro, listo para guardar en la BD.

    bcrypt añade una 'sal' aleatoria: por eso dos hashes de la misma contraseña
    salen distintos, pero ambos verifican correctamente.
    """
    hash_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    """Comprueba si una contraseña coincide con su hash guardado."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def crear_token(usuario_id: uuid.UUID) -> str:
    """Crea un JWT firmado que identifica al usuario.

    El token lleva 'sub' (subject = quién es) y 'exp' (cuándo caduca). El rol NO
    se guarda: se consulta siempre en la BD (fresco), igual que el estado activo.
    """
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "exp": ahora + timedelta(minutes=JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Verifica la firma y la caducidad del token y devuelve su contenido.

    Lanza jwt.InvalidTokenError (o una subclase, p.ej. ExpiredSignatureError)
    si el token es inválido, fue manipulado o ya expiró.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


security = HTTPBearer()


def usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    """Valida el token del header y devuelve el usuario actual.

    Se usa como dependencia en los endpoints que requieren estar autenticado.
    Lanza 401 si el token es inválido/expiró o el usuario ya no existe.
    """
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
    """Fábrica de dependencias: exige que el usuario actual tenga uno de estos roles.

    Uso en un endpoint:  dependencies=[Depends(requiere_rol(Rol.ADMIN))]
    Devuelve una dependencia que primero autentica (usuario_actual) y luego
    comprueba el rol; lanza 403 si no está permitido.
    """

    def verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta acción",
            )
        return usuario

    return verificar
