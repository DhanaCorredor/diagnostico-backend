"""Availability schemas (the doctor's weekly slots)."""
import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class AvailabilityOut(BaseModel):
    """One weekly availability slot of a doctor."""

    id: uuid.UUID
    medico_id: uuid.UUID = Field(validation_alias="usuario_id")
    dia_semana: int
    hora_inicio: time
    hora_fin: time

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AvailabilityCreate(BaseModel):
    """Body of POST /disponibilidad (define a slot for a doctor)."""

    medico_id: uuid.UUID
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    hora_fin: time
