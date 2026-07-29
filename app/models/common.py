"""Helpers shared by the models: uuid primary key and the N:M association tables."""
import uuid

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


def uuid_pk():
    """Id column: uuid primary key generated in Python (uuid4)."""
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


user_specialty = Table(
    "usuario_especialidad",
    Base.metadata,
    Column("usuario_id", UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True),
    Column("especialidad_id", UUID(as_uuid=True), ForeignKey("especialidades.id"), primary_key=True),
)


service_specialty = Table(
    "servicio_especialidad",
    Base.metadata,
    Column("servicio_id", UUID(as_uuid=True), ForeignKey("servicios.id"), primary_key=True),
    Column("especialidad_id", UUID(as_uuid=True), ForeignKey("especialidades.id"), primary_key=True),
)
