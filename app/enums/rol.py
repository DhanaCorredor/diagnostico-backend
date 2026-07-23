"""Rol de un usuario del sistema."""
import enum


class Rol(str, enum.Enum):
    ADMIN = "ADMIN"
    RECEPCION = "RECEPCION"
    MEDICO = "MEDICO"
    PACIENTE = "PACIENTE"
