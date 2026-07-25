"""Esquemas de disponibilidad (franjas semanales del médico)."""
import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class AvailabilityOut(BaseModel):
    """Una franja de disponibilidad semanal de un médico."""

    id: uuid.UUID
    medico_id: uuid.UUID = Field(validation_alias="usuario_id")
    dia_semana: int
    hora_inicio: time
    hora_fin: time

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AvailabilityCreate(BaseModel):
    """Cuerpo del POST /disponibilidad (definir una franja de un médico)."""

    medico_id: uuid.UUID
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    hora_fin: time
