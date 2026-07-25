"""Modelo Usuario: persona única (personal, médicos y pacientes) diferenciada por `rol`."""
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db import Base
from app.enums.role import Role
from app.models.common import user_specialty, uuid_pk


class User(Base):
    """Personal, médicos y pacientes comparten esta tabla; los campos que no aplican quedan a NULL."""

    __tablename__ = "usuarios"

    id = uuid_pk()
    nombre_completo = Column(String, nullable=False)
    rol = Column(Enum(Role, name="rol"), nullable=False)

    email = Column(String, unique=True)
    password_hash = Column(String)

    cedula = Column(String, unique=True)
    edad = Column(Integer)
    fecha_nacimiento = Column(Date)
    telefono = Column(String)

    matricula = Column(String)

    alergias = Column(Text)
    antecedentes = Column(Text)

    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    especialidades = relationship(
        "Specialty", secondary=user_specialty, back_populates="medicos"
    )
