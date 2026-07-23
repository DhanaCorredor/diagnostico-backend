"""Esquemas de pacientes."""
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PacienteOut(BaseModel):
    """Datos de un paciente (lista y ficha)."""

    id: uuid.UUID
    nombre_completo: str
    edad: int | None
    cedula: str | None
    telefono: str | None
    fecha_nacimiento: date | None

    model_config = ConfigDict(from_attributes=True)


class PacienteCreate(BaseModel):
    """Cuerpo del POST /pacientes: alta manual (sin agendarle cita)."""

    nombre_completo: str = Field(min_length=1)
    edad: int = Field(ge=0, le=120)
    cedula: str | None = None
    telefono: str | None = None
    fecha_nacimiento: date | None = None


class PacienteUpdate(PacienteCreate):
    """Cuerpo del PUT /pacientes/{id}: mismos campos que el alta."""
