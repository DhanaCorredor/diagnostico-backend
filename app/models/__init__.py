"""Modelos SQLAlchemy (las 7 tablas del sistema). Ver docs/MODELO-DATOS.md."""
from app.models.appointment import Appointment
from app.models.common import servicio_especialidad, usuario_especialidad
from app.models.availability import Availability
from app.models.specialty import Specialty
from app.models.clinical_note import ClinicalNote
from app.models.service import Service
from app.models.user import User

__all__ = [
    "Appointment",
    "Availability",
    "Specialty",
    "ClinicalNote",
    "Service",
    "User",
    "servicio_especialidad",
    "usuario_especialidad",
]
