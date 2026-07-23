"""Esquemas del catálogo: servicios, especialidades y médicos."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.enums import ServicioCategoria


class ServicioOut(BaseModel):
    """Un servicio del catálogo (para el formulario de cita)."""

    id: uuid.UUID
    nombre: str
    categoria: ServicioCategoria

    model_config = ConfigDict(from_attributes=True)


class ServicioDetalle(ServicioOut):
    """`ServicioOut` + `activo` (gestión del ADMIN)."""

    activo: bool


class ServicioCreate(BaseModel):
    """Cuerpo del POST /servicios."""

    nombre: str = Field(min_length=1)
    categoria: ServicioCategoria


class ServicioUpdate(BaseModel):
    """Cuerpo del PUT /servicios/{id}. Solo se cambian los campos enviados."""

    nombre: str | None = Field(default=None, min_length=1)
    categoria: ServicioCategoria | None = None
    activo: bool | None = None


class EspecialidadOut(BaseModel):
    """Una especialidad médica."""

    id: uuid.UUID
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class EspecialidadCreate(BaseModel):
    """Cuerpo del POST /especialidades."""

    nombre: str = Field(min_length=1)


class MedicoOut(BaseModel):
    """Un médico con sus especialidades (para elegir médico al agendar)."""

    id: uuid.UUID
    nombre_completo: str
    especialidades: list[EspecialidadOut]

    model_config = ConfigDict(from_attributes=True)
