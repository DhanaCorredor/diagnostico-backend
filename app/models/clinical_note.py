"""ClinicalNote model: minimal medical history (scaffolding, reserved for phase 2)."""
from sqlalchemy import Column, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base
from app.models.common import uuid_pk


class ClinicalNote(Base):
    """Free-text note a doctor writes about a patient (no functionality in the MVP)."""

    __tablename__ = "notas_clinicas"

    id = uuid_pk()
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    medico_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    cita_id = Column(UUID(as_uuid=True), ForeignKey("citas.id"))
    fecha = Column(DateTime, nullable=False, default=func.now())
    contenido = Column(Text, nullable=False)
