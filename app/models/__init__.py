"""Modelos SQLAlchemy (las 7 tablas del sistema). Ver docs/MODELO-DATOS.md."""
from app.models.appointment import Appointment
from app.models.availability import Availability
from app.models.clinical_note import ClinicalNote
from app.models.common import service_specialty, user_specialty
from app.models.service import Service
from app.models.specialty import Specialty
from app.models.user import User

__all__ = [
    "Appointment",
    "Availability",
    "Specialty",
    "ClinicalNote",
    "Service",
    "User",
    "service_specialty",
    "user_specialty",
]
