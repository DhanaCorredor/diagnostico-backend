"""Piezas de seguridad: hash de contraseñas (bcrypt) y tokens JWT (PyJWT).

Son funciones reutilizables, sin endpoints. Los routers de la Fase 2 las usan
para el login y para verificar el token en cada petición.
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

# Secreto para firmar los tokens: viene del .env (nunca hardcodeado).
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"        # algoritmo de firma (HMAC + SHA-256)
JWT_EXPIRA_MINUTOS = 60 * 8    # el token dura 8 horas (una jornada laboral)


# --- Contraseñas (bcrypt) ---------------------------------------------------


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


# --- Tokens JWT (PyJWT) -----------------------------------------------------


def crear_token(usuario_id: str, rol: str) -> str:
    """Crea un JWT firmado que identifica al usuario y su rol.

    El token lleva 'sub' (subject = quién es), 'rol' y 'exp' (cuándo caduca).
    """
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "rol": rol,
        "exp": ahora + timedelta(minutes=JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Verifica la firma y la caducidad del token y devuelve su contenido.

    Lanza jwt.InvalidTokenError (o una subclase, p.ej. ExpiredSignatureError)
    si el token es inválido, fue manipulado o ya expiró.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
