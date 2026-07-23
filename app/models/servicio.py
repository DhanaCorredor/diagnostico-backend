"""Modelo Servicio: catálogo de consultas y estudios."""
from sqlalchemy import Boolean, Column, Enum, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.enums.servicio_categoria import ServicioCategoria
from app.models.comun import servicio_especialidad, uuid_pk


class Servicio(Base):
    """Servicio del catálogo; se relaciona N:M con las especialidades que lo ofrecen."""

    __tablename__ = "servicios"

    id = uuid_pk()
    nombre = Column(String, unique=True, nullable=False)
    categoria = Column(Enum(ServicioCategoria), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)

    especialidades = relationship(
        "Especialidad", secondary=servicio_especialidad, back_populates="servicios"
    )
