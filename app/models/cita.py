"""Modelo Cita: el núcleo del sistema (anti-solapamiento por médico)."""
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base
from app.enums.appointment_status import AppointmentStatus
from app.models.comun import uuid_pk


class Cita(Base):
    """Cita médica: paciente + médico + servicio en una franja, con estado y auditoría mínima."""

    __tablename__ = "citas"

    id = uuid_pk()
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    medico_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    estado = Column(
        Enum(AppointmentStatus, name="estadocita"),
        nullable=False,
        default=AppointmentStatus.SCHEDULED,
    )
    motivo = Column(String)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
