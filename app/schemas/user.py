"""Staff schemas (the users who log in)."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.enums import Role
from app.schemas.catalog import SpecialtyOut


class UserOut(BaseModel):
    """Public user data (never includes the password_hash)."""

    id: uuid.UUID
    nombre_completo: str
    email: str | None
    rol: Role

    model_config = ConfigDict(from_attributes=True)


class UserDetail(BaseModel):
    """Data of a staff user (list/detail), with specialties if they are a doctor."""

    id: uuid.UUID
    nombre_completo: str
    email: str | None
    rol: Role
    matricula: str | None
    especialidades: list[SpecialtyOut]
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Registration of staff/doctor (ADMIN). The role cannot be PACIENTE (validated in the service)."""

    nombre_completo: str = Field(min_length=1)
    rol: Role
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)
    matricula: str | None = None
    especialidades: list[uuid.UUID] = []


class UserUpdate(BaseModel):
    """Partial edit of a staff user. Only the fields sent are changed."""

    nombre_completo: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=3)
    password: str | None = Field(default=None, min_length=8)
    matricula: str | None = None
    especialidades: list[uuid.UUID] | None = None
    activo: bool | None = None


class UserErased(BaseModel):
    """Response of DELETE /usuarios/{id}: what happened to the record.

    `resultado` is `eliminado` when nothing was left, or `anonimizado` when the personal data was
    wiped but their past appointments were kept.
    """

    resultado: str
    citas_conservadas: int
