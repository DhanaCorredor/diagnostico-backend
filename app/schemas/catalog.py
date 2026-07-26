"""Esquemas del catálogo: servicios, especialidades y médicos."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.enums import ServiceCategory


class SpecialtyOut(BaseModel):
    """Una especialidad médica."""

    id: uuid.UUID
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class SpecialtyCreate(BaseModel):
    """Cuerpo del POST /especialidades."""

    nombre: str = Field(min_length=1)


class ServiceOut(BaseModel):
    """Un servicio del catálogo con las especialidades que lo ofrecen (para el formulario de cita)."""

    id: uuid.UUID
    nombre: str
    categoria: ServiceCategory
    especialidades: list[SpecialtyOut]

    model_config = ConfigDict(from_attributes=True)


class ServiceDetail(ServiceOut):
    """`ServicioOut` + `activo` (gestión del ADMIN)."""

    activo: bool


class ServiceCreate(BaseModel):
    """Cuerpo del POST /servicios."""

    nombre: str = Field(min_length=1)
    categoria: ServiceCategory


class ServiceUpdate(BaseModel):
    """Cuerpo del PUT /servicios/{id}. Solo se cambian los campos enviados."""

    nombre: str | None = Field(default=None, min_length=1)
    categoria: ServiceCategory | None = None
    activo: bool | None = None


class DoctorOut(BaseModel):
    """Un médico con sus especialidades (para elegir médico al agendar)."""

    id: uuid.UUID
    nombre_completo: str
    especialidades: list[SpecialtyOut]

    model_config = ConfigDict(from_attributes=True)
