"""Modelo Servicio: catálogo de consultas y estudios."""
from sqlalchemy import Boolean, Column, Enum, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.enums.service_category import ServiceCategory
from app.models.common import service_specialty, uuid_pk


class Service(Base):
    """Servicio del catálogo; se relaciona N:M con las especialidades que lo ofrecen."""

    __tablename__ = "servicios"

    id = uuid_pk()
    nombre = Column(String, unique=True, nullable=False)
    categoria = Column(Enum(ServiceCategory, name="serviciocategoria"), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)

    especialidades = relationship(
        "Specialty", secondary=service_specialty, back_populates="servicios"
    )
