"""Modelos SQLAlchemy: las tablas de la base de datos como clases de Python.

Cada clase hereda de `Base` (definida en db.py). SQLAlchemy usa estas clases
para crear las tablas y para traducir entre filas de la BD y objetos Python.

El modelo completo (7 tablas) está documentado en docs/MODELO-DATOS.md.
"""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


# --- Enums: listas cerradas de valores permitidos ---------------------------
# Heredan de `str` para que su valor en la BD sea el texto (ej. "ADMIN"),
# legible y fácil de comparar.


class Rol(str, enum.Enum):
    ADMIN = "ADMIN"
    RECEPCION = "RECEPCION"
    MEDICO = "MEDICO"
    PACIENTE = "PACIENTE"


class EstadoCita(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class ServicioCategoria(str, enum.Enum):
    CONSULTA = "CONSULTA"
    ECOGRAFIA = "ECOGRAFIA"
    ESTUDIO_CARDIACO = "ESTUDIO_CARDIACO"
    OTRO = "OTRO"


def _uuid_pk():
    """Columna id: clave primaria uuid generada en Python (uuid4).

    Se repite en las 7 tablas, así que se centraliza aquí. Cada llamada
    devuelve una Column nueva (SQLAlchemy no permite reutilizar la misma).
    """
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# --- Tabla de asociación N:M: médico <-> especialidad -----------------------
# No tiene columnas propias, solo las dos claves foráneas, así que se define
# como una Table simple (no como clase). Su PK es la pareja (usuario, especialidad).
usuario_especialidad = Table(
    "usuario_especialidad",
    Base.metadata,
    Column("usuario_id", UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True),
    Column("especialidad_id", UUID(as_uuid=True), ForeignKey("especialidades.id"), primary_key=True),
)


# --- Tablas principales ------------------------------------------------------


class Usuario(Base):
    """Persona única: personal, médicos y pacientes comparten esta tabla.

    Se diferencian por el campo `rol`. Los campos que no aplican a un rol
    quedan a NULL (ej. un paciente no tiene email ni password_hash).
    """

    __tablename__ = "usuarios"

    id = _uuid_pk()
    nombre_completo = Column(String, nullable=False)
    rol = Column(Enum(Rol), nullable=False)

    # Login (solo personal interno: ADMIN, RECEPCION, MEDICO)
    email = Column(String, unique=True)   # opcional; único si se indica
    password_hash = Column(String)        # bcrypt; solo staff

    # Identificación / datos de la persona
    cedula = Column(String, unique=True)  # opcional; la añaden los especialistas después
    edad = Column(Integer)                # edad al registrar (lo que pide recepción)
    fecha_nacimiento = Column(Date)       # opcional; se completa luego
    telefono = Column(String)             # varios pacientes pueden compartir número

    # Solo médico
    matricula = Column(String)            # nº de colegiado

    # Historia clínica (solo paciente)
    alergias = Column(Text)
    antecedentes = Column(Text)

    activo = Column(Boolean, nullable=False, default=True)  # baja lógica
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Especialidades del médico (relación N:M vía la tabla de asociación)
    especialidades = relationship(
        "Especialidad", secondary=usuario_especialidad, back_populates="medicos"
    )


class Especialidad(Base):
    """Especialidad médica (ej. Cardiología)."""

    __tablename__ = "especialidades"

    id = _uuid_pk()
    nombre = Column(String, unique=True, nullable=False)

    medicos = relationship(
        "Usuario", secondary=usuario_especialidad, back_populates="especialidades"
    )


class Servicio(Base):
    """Catálogo de consultas y estudios. La duración marca el `ends_at` de la cita."""

    __tablename__ = "servicios"

    id = _uuid_pk()
    nombre = Column(String, unique=True, nullable=False)
    categoria = Column(Enum(ServicioCategoria), nullable=False)
    duracion_min = Column(Integer, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)


class Disponibilidad(Base):
    """Franja horaria semanal en la que un médico atiende."""

    __tablename__ = "disponibilidad"

    id = _uuid_pk()
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)  # médico
    dia_semana = Column(Integer, nullable=False)  # 0=domingo ... 6=sábado
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)


class Cita(Base):
    """La cita médica (núcleo del sistema). Anti-solapamiento por médico en el servicio."""

    __tablename__ = "citas"

    id = _uuid_pk()
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    medico_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)  # = starts_at + servicios.duracion_min
    estado = Column(Enum(EstadoCita), nullable=False, default=EstadoCita.SCHEDULED)
    motivo = Column(String)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)  # recepción
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class NotaClinica(Base):
    """Historia clínica mínima: nota de texto que el médico escribe sobre un paciente."""

    __tablename__ = "notas_clinicas"

    id = _uuid_pk()
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    medico_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)  # quién la escribe
    cita_id = Column(UUID(as_uuid=True), ForeignKey("citas.id"))  # opcional
    fecha = Column(DateTime, nullable=False, default=func.now())
    contenido = Column(Text, nullable=False)
