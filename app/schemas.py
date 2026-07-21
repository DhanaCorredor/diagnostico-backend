"""Esquemas Pydantic: los 'moldes' de entrada y salida de la API.

Pydantic valida el JSON que entra y da forma al JSON que sale (y con ello la
documentación automática de /docs).
"""

import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoCita, Rol, ServicioCategoria


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

    # Permite construir el esquema a partir de un objeto ORM (usuario.id, .rol...).
    model_config = ConfigDict(from_attributes=True)


class ServicioOut(BaseModel):
    """Un servicio del catálogo (para el formulario de cita)."""

    id: uuid.UUID
    nombre: str
    categoria: ServicioCategoria

    model_config = ConfigDict(from_attributes=True)


class ServicioDetalle(BaseModel):
    """Un servicio con su estado (para la gestión del ADMIN: incluye `activo`)."""

    id: uuid.UUID
    nombre: str
    categoria: ServicioCategoria
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class ServicioCreate(BaseModel):
    """Cuerpo del POST /servicios: alta de un servicio en el catálogo."""

    nombre: str = Field(min_length=1)
    categoria: ServicioCategoria


class ServicioUpdate(BaseModel):
    """Cuerpo del PUT /servicios/{id}. Solo se cambian los campos enviados."""

    nombre: str | None = Field(default=None, min_length=1)
    categoria: ServicioCategoria | None = None
    activo: bool | None = None  # permite desactivar el servicio sin borrarlo


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
    medico_id: uuid.UUID = Field(validation_alias="usuario_id")  # el modelo la guarda como usuario_id
    dia_semana: int
    hora_inicio: time
    hora_fin: time

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DisponibilidadCreate(BaseModel):
    """Cuerpo del POST /disponibilidad (definir una franja de un médico)."""

    medico_id: uuid.UUID
    dia_semana: int = Field(ge=0, le=6)  # 0=domingo ... 6=sábado
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


class PacienteUpdate(BaseModel):
    """Cuerpo del PUT /pacientes/{id}. No incluye rol (fijo PACIENTE) ni datos clínicos."""

    nombre_completo: str = Field(min_length=1)
    edad: int = Field(ge=0, le=120)
    cedula: str | None = None
    telefono: str | None = None
    fecha_nacimiento: date | None = None


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
    activo: bool | None = None  # PUT {"activo": true} reactiva un usuario dado de baja


class CitaCreate(BaseModel):
    """Cuerpo del POST /citas. El paciente se identifica por nombre + edad (upsert)."""

    nombre_completo: str = Field(min_length=1)  # no puede ir vacío
    edad: int = Field(ge=0, le=120)             # 0 (lactantes) a 120
    medico_id: uuid.UUID
    servicio_id: uuid.UUID
    starts_at: datetime
    duracion_min: Literal[15, 30, 45, 60, 90]  # la elige recepción; solo estos valores
    motivo: str | None = None
    permitir_sobrecupo: bool = False  # recepción puede forzar un cupo extra


class CitaUpdate(BaseModel):
    """Cuerpo del PUT /citas/{id}: editar o mover una cita. Todos los campos son
    opcionales; solo se aplican los enviados (None = sin cambio). No cambia el paciente."""

    medico_id: uuid.UUID | None = None
    servicio_id: uuid.UUID | None = None
    starts_at: datetime | None = None
    duracion_min: Literal[15, 30, 45, 60, 90] | None = None
    motivo: str | None = None
    permitir_sobrecupo: bool = False  # recepción puede forzar un cupo extra al mover


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
