"""Esquemas Pydantic: los 'moldes' de entrada y salida de la API.

Pydantic valida el JSON que entra y da forma al JSON que sale (y con ello la
documentación automática de /docs).
"""

import uuid

from pydantic import BaseModel, ConfigDict

from app.models import Rol


class LoginRequest(BaseModel):
    """Cuerpo del POST /auth/login."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta del login: el token JWT."""

    access_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    """Datos públicos del usuario (nunca incluye el password_hash)."""

    id: uuid.UUID
    nombre_completo: str
    email: str | None
    rol: Rol

    # Permite construir el esquema a partir de un objeto ORM (usuario.id, .rol...).
    model_config = ConfigDict(from_attributes=True)
