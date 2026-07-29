"""Role of a system user."""
import enum


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    RECEPCION = "RECEPCION"
    MEDICO = "MEDICO"
    PACIENTE = "PACIENTE"
