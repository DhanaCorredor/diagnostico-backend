"""Rol de un usuario del sistema."""
import enum


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    RECEPCION = "RECEPCION"
    MEDICO = "MEDICO"
    PACIENTE = "PACIENTE"
