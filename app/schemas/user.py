"""Esquemas del personal (usuarios que hacen login)."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.enums import Role
from app.schemas.catalog import SpecialtyOut


class UserOut(BaseModel):
    """Datos públicos del usuario (nunca incluye el password_hash)."""

    id: uuid.UUID
    nombre_completo: str
    email: str | None
    rol: Role

    model_config = ConfigDict(from_attributes=True)


class UserDetail(BaseModel):
    """Datos de un usuario del personal (lista/ficha), con especialidades si es médico."""

    id: uuid.UUID
    nombre_completo: str
    email: str | None
    rol: Role
    matricula: str | None
    especialidades: list[SpecialtyOut]
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Alta de personal/médico (ADMIN). El rol no puede ser PACIENTE (se valida en el servicio)."""

    nombre_completo: str = Field(min_length=1)
    rol: Role
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)
    matricula: str | None = None
    especialidades: list[uuid.UUID] = []


class UserUpdate(BaseModel):
    """Edición parcial de un usuario del personal. Solo se cambian los campos enviados."""

    nombre_completo: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=3)
    password: str | None = Field(default=None, min_length=8)
    matricula: str | None = None
    especialidades: list[uuid.UUID] | None = None
    activo: bool | None = None
