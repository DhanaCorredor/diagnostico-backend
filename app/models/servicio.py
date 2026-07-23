"""Modelo Servicio: catálogo de consultas y estudios."""
from sqlalchemy import Boolean, Column, Enum, String

from app.db import Base
from app.enums.servicio_categoria import ServicioCategoria
from app.models.comun import uuid_pk


class Servicio(Base):
    """Servicio del catálogo; la duración de la cita la elige recepción al agendar."""

    __tablename__ = "servicios"

    id = uuid_pk()
    nombre = Column(String, unique=True, nullable=False)
    categoria = Column(Enum(ServicioCategoria), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
