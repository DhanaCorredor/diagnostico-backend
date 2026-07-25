"""Esquemas de citas, incluida la validación de la hora local del centro."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import AppointmentStatus


def _exigir_hora_local_naive(v: datetime | None) -> datetime | None:
    """Exige hora local naive (sin zona); una fecha con zona horaria se rechaza."""
    if v is not None and v.tzinfo is not None:
        raise ValueError("La fecha debe ir en hora local del centro, sin zona horaria.")
    return v


class AppointmentCreate(BaseModel):
    """Cuerpo del POST /citas: identifica al paciente por nombre + edad (upsert) o por `paciente_id`."""

    nombre_completo: str = Field(min_length=1)
    edad: int = Field(ge=0, le=120)
    paciente_id: uuid.UUID | None = None
    medico_id: uuid.UUID
    servicio_id: uuid.UUID
    starts_at: datetime
    duracion_min: Literal[15, 30, 45, 60, 90]
    motivo: str | None = None
    permitir_sobrecupo: bool = False

    @field_validator("starts_at")
    @classmethod
    def _starts_at_local_naive(cls, v: datetime) -> datetime:
        return _exigir_hora_local_naive(v)


class AppointmentUpdate(BaseModel):
    """PUT /citas/{id}: editar o mover. Campos opcionales; None = sin cambio. No cambia el paciente."""

    medico_id: uuid.UUID | None = None
    servicio_id: uuid.UUID | None = None
    starts_at: datetime | None = None
    duracion_min: Literal[15, 30, 45, 60, 90] | None = None
    motivo: str | None = None
    permitir_sobrecupo: bool = False

    @field_validator("starts_at")
    @classmethod
    def _starts_at_local_naive(cls, v: datetime | None) -> datetime | None:
        return _exigir_hora_local_naive(v)


class AppointmentOut(BaseModel):
    """Datos de la cita creada."""

    id: uuid.UUID
    paciente_id: uuid.UUID
    medico_id: uuid.UUID
    servicio_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    estado: AppointmentStatus
    motivo: str | None

    model_config = ConfigDict(from_attributes=True)


class AttendanceUpdate(BaseModel):
    """POST /citas/{id}/asistencia: marcar atendida o no-show."""

    estado: Literal[AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW]
