"""Utilidades compartidas por los modelos: PK uuid y las tablas de asociación N:M."""
import uuid

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


def uuid_pk():
    """Columna id: clave primaria uuid generada en Python (uuid4)."""
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


usuario_especialidad = Table(
    "usuario_especialidad",
    Base.metadata,
    Column("usuario_id", UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True),
    Column("especialidad_id", UUID(as_uuid=True), ForeignKey("especialidades.id"), primary_key=True),
)


servicio_especialidad = Table(
    "servicio_especialidad",
    Base.metadata,
    Column("servicio_id", UUID(as_uuid=True), ForeignKey("servicios.id"), primary_key=True),
    Column("especialidad_id", UUID(as_uuid=True), ForeignKey("especialidades.id"), primary_key=True),
)
