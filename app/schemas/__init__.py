"""Pydantic schemas (API input/output), grouped by domain."""
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentUpdate,
    AttendanceUpdate,
)
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.availability import AvailabilityCreate, AvailabilityOut, AvailabilityUpdate
from app.schemas.catalog import (
    DoctorOut,
    ServiceCreate,
    ServiceDetail,
    ServiceOut,
    ServiceUpdate,
    SpecialtyCreate,
    SpecialtyOut,
    SpecialtyUpdate,
)
from app.schemas.patient import PatientCreate, PatientErased, PatientOut, PatientUpdate
from app.schemas.user import UserCreate, UserDetail, UserOut, UserUpdate

__all__ = [
    "AppointmentCreate",
    "AppointmentOut",
    "AppointmentUpdate",
    "AttendanceUpdate",
    "AvailabilityCreate",
    "AvailabilityOut",
    "AvailabilityUpdate",
    "DoctorOut",
    "LoginRequest",
    "PatientCreate",
    "PatientErased",
    "PatientOut",
    "PatientUpdate",
    "ServiceCreate",
    "ServiceDetail",
    "ServiceOut",
    "ServiceUpdate",
    "SpecialtyCreate",
    "SpecialtyOut",
    "SpecialtyUpdate",
    "TokenResponse",
    "UserCreate",
    "UserDetail",
    "UserOut",
    "UserUpdate",
]
