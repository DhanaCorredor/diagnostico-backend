"""Catalog schemas: services, specialties and doctors."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.enums import ServiceCategory


class SpecialtyOut(BaseModel):
    """A medical specialty."""

    id: uuid.UUID
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class SpecialtyCreate(BaseModel):
    """Body of POST /especialidades."""

    nombre: str = Field(min_length=1)


class ServiceOut(BaseModel):
    """A catalog service with the specialties that offer it (for the appointment form)."""

    id: uuid.UUID
    nombre: str
    categoria: ServiceCategory
    especialidades: list[SpecialtyOut]

    model_config = ConfigDict(from_attributes=True)


class ServiceDetail(ServiceOut):
    """`ServicioOut` + `activo` (ADMIN management)."""

    activo: bool


class ServiceCreate(BaseModel):
    """Body of POST /servicios."""

    nombre: str = Field(min_length=1)
    categoria: ServiceCategory


class ServiceUpdate(BaseModel):
    """Body of PUT /servicios/{id}. Only the fields sent are changed.

    `especialidades` replaces the whole list of specialties that offer the service; sending an
    empty list unlinks them all, which is what drives the "services of this doctor" filter.
    """

    nombre: str | None = Field(default=None, min_length=1)
    categoria: ServiceCategory | None = None
    activo: bool | None = None
    especialidades: list[uuid.UUID] | None = None


class DoctorOut(BaseModel):
    """A doctor with their specialties (to pick a doctor when scheduling)."""

    id: uuid.UUID
    nombre_completo: str
    especialidades: list[SpecialtyOut]

    model_config = ConfigDict(from_attributes=True)


class SpecialtyUpdate(BaseModel):
    """Body of PUT /especialidades/{id}: the only editable field is the name."""

    nombre: str = Field(min_length=1)
