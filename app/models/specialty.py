"""Specialty model (e.g. Cardiology)."""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.common import service_specialty, user_specialty, uuid_pk


class Specialty(Base):
    """Medical specialty; N:M with the doctors who practice it and the services it covers."""

    __tablename__ = "especialidades"

    id = uuid_pk()
    nombre = Column(String, unique=True, nullable=False)

    medicos = relationship(
        "User", secondary=user_specialty, back_populates="especialidades"
    )
    servicios = relationship(
        "Service", secondary=service_specialty, back_populates="especialidades"
    )
