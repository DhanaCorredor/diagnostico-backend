"""Modelo Especialidad (ej. Cardiología)."""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.common import service_specialty, user_specialty, uuid_pk


class Specialty(Base):
    """Especialidad médica; N:M con los médicos que la ejercen y con los servicios que abarca."""

    __tablename__ = "especialidades"

    id = uuid_pk()
    nombre = Column(String, unique=True, nullable=False)

    medicos = relationship(
        "User", secondary=user_specialty, back_populates="especialidades"
    )
    servicios = relationship(
        "Service", secondary=service_specialty, back_populates="especialidades"
    )
