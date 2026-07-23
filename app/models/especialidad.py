"""Modelo Especialidad (ej. Cardiología)."""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.comun import usuario_especialidad, uuid_pk


class Especialidad(Base):
    """Especialidad médica; se relaciona N:M con los médicos que la ejercen."""

    __tablename__ = "especialidades"

    id = uuid_pk()
    nombre = Column(String, unique=True, nullable=False)

    medicos = relationship(
        "Usuario", secondary=usuario_especialidad, back_populates="especialidades"
    )
