"""Modelo Especialidad (ej. Cardiología)."""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.comun import servicio_especialidad, usuario_especialidad, uuid_pk


class Especialidad(Base):
    """Especialidad médica; N:M con los médicos que la ejercen y con los servicios que abarca."""

    __tablename__ = "especialidades"

    id = uuid_pk()
    nombre = Column(String, unique=True, nullable=False)

    medicos = relationship(
        "Usuario", secondary=usuario_especialidad, back_populates="especialidades"
    )
    servicios = relationship(
        "Servicio", secondary=servicio_especialidad, back_populates="especialidades"
    )
