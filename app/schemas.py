"""Esquemas Pydantic: los 'moldes' de entrada y salida de la API.

Pydantic valida el JSON que entra y da forma al JSON que sale (y con ello la
documentación automática de /docs).
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoCita, Rol


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


class CitaCreate(BaseModel):
    """Cuerpo del POST /citas. El paciente se identifica por nombre + edad (upsert)."""

    nombre_completo: str = Field(min_length=1)  # no puede ir vacío
    edad: int = Field(ge=0, le=120)             # 0 (lactantes) a 120
    medico_id: uuid.UUID
    servicio_id: uuid.UUID
    starts_at: datetime
    duracion_min: Literal[15, 30, 45, 60, 90]  # la elige recepción; solo estos valores
    motivo: str | None = None
    permitir_sobrecupo: bool = False  # recepción puede forzar un cupo extra


class CitaOut(BaseModel):
    """Datos de la cita creada."""

    id: uuid.UUID
    paciente_id: uuid.UUID
    medico_id: uuid.UUID
    servicio_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    estado: EstadoCita
    motivo: str | None

    model_config = ConfigDict(from_attributes=True)
