"""Modelo NotaClinica: historia clínica mínima (andamiaje, reservada para fase 2)."""
from sqlalchemy import Column, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base
from app.models.comun import uuid_pk


class ClinicalNote(Base):
    """Nota de texto que el médico escribe sobre un paciente (sin funcionalidad en el MVP)."""

    __tablename__ = "notas_clinicas"

    id = uuid_pk()
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    medico_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    cita_id = Column(UUID(as_uuid=True), ForeignKey("citas.id"))
    fecha = Column(DateTime, nullable=False, default=func.now())
    contenido = Column(Text, nullable=False)
