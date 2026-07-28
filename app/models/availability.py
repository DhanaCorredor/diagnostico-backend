"""Availability model: the weekly time slot in which a doctor sees patients."""
from sqlalchemy import Column, ForeignKey, Integer, Time
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base
from app.models.common import uuid_pk


class Availability(Base):
    """Weekly slot (day + start/end time) of a doctor; the calendar uses it to block bookings."""

    __tablename__ = "disponibilidad"

    id = uuid_pk()
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    dia_semana = Column(Integer, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
