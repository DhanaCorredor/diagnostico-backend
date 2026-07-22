"""Esquemas Pydantic: los 'moldes' de entrada y salida de la API.

Pydantic valida el JSON que entra y da forma al JSON que sale (y con ello la
documentación automática de /docs).
"""

import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import EstadoCita, Rol, ServicioCategoria


def _exigir_hora_local_naive(v: datetime | None) -> datetime | None:
    """Exige que la fecha/hora llegue SIN zona horaria (naive), en hora local del centro.

    La API trabaja en la hora de reloj del centro (sede única, una sola zona) y guarda
    las fechas sin zona. Si llega una fecha CON zona (p. ej. la 'Z' que añade
    `Date.toISOString()` en el navegador) se RECHAZA, en vez de convertirla a ciegas:
    así el frontend manda siempre la hora local explícita y no hay ambigüedad de zona.
    Contrato: el frontend envía la hora local del centro, sin sufijo de zona.
    """
    if v is not None and v.tzinfo is not None:
        raise ValueError("La fecha debe ir en hora local del centro, sin zona horaria.")
    return v


class LoginRequest(BaseModel):
    """Cuerpo del POST /auth/login."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta del login: el token JWT."""

    access_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    """Datos públicos del usuario (nunca incluye el password_hash)."""

    id: uuid.UUID
    nombre_completo: str
    email: str | None
    rol: Rol

    model_config = ConfigDict(from_attributes=True)


class ServicioOut(BaseModel):
    """Un servicio del catálogo (para el formulario de cita)."""

    id: uuid.UUID
    nombre: str
    categoria: ServicioCategoria

    model_config = ConfigDict(from_attributes=True)


class ServicioDetalle(ServicioOut):
    """Un servicio con su estado (para la gestión del ADMIN: `ServicioOut` + `activo`)."""

    activo: bool


class ServicioCreate(BaseModel):
    """Cuerpo del POST /servicios: alta de un servicio en el catálogo."""

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
    """Cuerpo del POST /especialidades: alta de una especialidad."""

    nombre: str = Field(min_length=1)


class MedicoOut(BaseModel):
    """Un médico con sus especialidades (para elegir médico al agendar)."""

    id: uuid.UUID
    nombre_completo: str
    especialidades: list[EspecialidadOut]

    model_config = ConfigDict(from_attributes=True)


class DisponibilidadOut(BaseModel):
    """Una franja de disponibilidad semanal de un médico."""

    id: uuid.UUID
    medico_id: uuid.UUID = Field(validation_alias="usuario_id")
    dia_semana: int
    hora_inicio: time
    hora_fin: time

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DisponibilidadCreate(BaseModel):
    """Cuerpo del POST /disponibilidad (definir una franja de un médico)."""

    medico_id: uuid.UUID
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    hora_fin: time


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
    """Cuerpo del POST /pacientes: alta manual de un paciente (sin agendarle cita)."""

    nombre_completo: str = Field(min_length=1)
    edad: int = Field(ge=0, le=120)
    cedula: str | None = None
    telefono: str | None = None
    fecha_nacimiento: date | None = None


class PacienteUpdate(PacienteCreate):
    """Cuerpo del PUT /pacientes/{id}: mismos campos que el alta (rol fijo PACIENTE, sin datos clínicos)."""


class UsuarioDetalle(BaseModel):
    """Datos de un usuario del personal (lista y ficha). Con especialidades si es médico."""

    id: uuid.UUID
    nombre_completo: str
    email: str | None
    rol: Rol
    matricula: str | None
    especialidades: list[EspecialidadOut]
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreate(BaseModel):
    """Alta de personal/médico (ADMIN). El rol no puede ser PACIENTE (se valida en el servicio)."""

    nombre_completo: str = Field(min_length=1)
    rol: Rol
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)
    matricula: str | None = None
    especialidades: list[uuid.UUID] = []


class UsuarioUpdate(BaseModel):
    """Edición parcial de un usuario del personal. Solo se cambian los campos enviados."""

    nombre_completo: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=3)
    password: str | None = Field(default=None, min_length=8)
    matricula: str | None = None
    especialidades: list[uuid.UUID] | None = None
    activo: bool | None = None


class CitaCreate(BaseModel):
    """Cuerpo del POST /citas. El paciente se identifica por nombre + edad (upsert)."""

    nombre_completo: str = Field(min_length=1)
    edad: int = Field(ge=0, le=120)
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


class CitaUpdate(BaseModel):
    """Cuerpo del PUT /citas/{id}: editar o mover una cita. Todos los campos son
    opcionales; solo se aplican los enviados (None = sin cambio). No cambia el paciente."""

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


class CitaOut(BaseModel):
    """Datos de la cita creada."""

    id: uuid.UUID
    paciente_id: uuid.UUID
    medico_id: uuid.UUID
    servicio_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    estado: EstadoCita
    motivo: str | None

    model_config = ConfigDict(from_attributes=True)


class AsistenciaUpdate(BaseModel):
    """Cuerpo del POST /citas/{id}/asistencia: marcar atendida o no-show."""

    estado: Literal[EstadoCita.COMPLETED, EstadoCita.NO_SHOW]
