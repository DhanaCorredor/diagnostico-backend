"""Patient schemas."""
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PatientOut(BaseModel):
    """Patient data (list and detail view)."""

    id: uuid.UUID
    nombre_completo: str
    edad: int | None
    cedula: str | None
    telefono: str | None
    fecha_nacimiento: date | None

    model_config = ConfigDict(from_attributes=True)


class PatientCreate(BaseModel):
    """Body of POST /pacientes: manual registration (without scheduling an appointment)."""

    nombre_completo: str = Field(min_length=1)
    edad: int = Field(ge=0, le=120)
    cedula: str | None = None
    telefono: str | None = None
    fecha_nacimiento: date | None = None


class PatientErased(BaseModel):
    """Response of DELETE /pacientes/{id}: what happened to the record.

    `resultado` is `eliminado` when nothing was left, or `anonimizado` when the personal data was
    wiped but the appointments were kept.
    """

    resultado: str
    citas_conservadas: int


class PatientUpdate(PatientCreate):
    """Body of PUT /pacientes/{id}: same fields as the registration."""
