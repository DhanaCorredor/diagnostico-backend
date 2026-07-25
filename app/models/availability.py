"""Modelo Disponibilidad: franja horaria semanal en la que un médico atiende."""
from sqlalchemy import Column, ForeignKey, Integer, Time
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base
from app.models.comun import uuid_pk


class Availability(Base):
    """Franja semanal (día + hora inicio/fin) de un médico; el calendario la usa para bloquear."""

    __tablename__ = "disponibilidad"

    id = uuid_pk()
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    dia_semana = Column(Integer, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
