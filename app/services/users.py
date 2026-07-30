"""Management logic for the staff who log in (ADMIN/RECEPCION/MEDICO): CRUD, ADMIN only."""

import uuid
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.auth import hash_password
from app.enums import AppointmentStatus, Role
from app.models import Appointment, Availability, User
from app.services.appointments import now_center
from app.services.catalog import resolve_specialties
from app.services.common import value_in_use

ROLES_STAFF = (Role.ADMIN, Role.RECEPCION, Role.MEDICO)
ACTIVE_STATUSES = (AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED)
ERASED_NAME = "Usuario eliminado"


class UserNotFound(Exception):
    """There is no staff user with that id."""


class DuplicateEmail(Exception):
    """The email is already used by another user."""


class RoleNotAllowed(Exception):
    """The given role cannot be created here (e.g. PACIENTE)."""


class CannotEraseSelf(Exception):
    """A user cannot erase their own account, or they would lock themselves out."""


class UserHasUpcomingAppointments(Exception):
    """The doctor still has booked appointments ahead; they must be moved or cancelled first."""

    def __init__(self, count: int):
        self.count = count
        super().__init__(f"{count} upcoming appointments")


class DoctorOnlyData(Exception):
    """Specialties or a license number were given for a user who is not a doctor."""


def _email_in_use(db: Session, email: str, exclude_id: uuid.UUID | None = None) -> bool:
    return value_in_use(db, User, User.email, email, exclude_id)



def list_staff(db: Session) -> list[User]:
    """Return the staff (everyone except patients), ordered by name."""
    return (
        db.query(User)
        .options(selectinload(User.especialidades))
        .filter(User.rol != Role.PACIENTE)
        .order_by(User.nombre_completo)
        .all()
    )


def get_user(db: Session, usuario_id: uuid.UUID) -> User:
    """Return a staff user by id, or raise UserNotFound."""
    user = db.get(User, usuario_id)
    if user is None or user.rol == Role.PACIENTE:
        raise UserNotFound()
    return user


def create_user(
    db: Session,
    *,
    nombre_completo: str,
    rol: Role,
    email: str,
    password: str,
    matricula: str | None,
    especialidades: list[uuid.UUID],
) -> User:
    """Create a staff user. Validates role and email, hashes the password. Flush (no commit)."""
    if rol not in ROLES_STAFF:
        raise RoleNotAllowed()
    if rol != Role.MEDICO and (especialidades or matricula is not None):
        raise DoctorOnlyData()
    if _email_in_use(db, email):
        raise DuplicateEmail()
    spec = resolve_specialties(db, especialidades)

    user = User(
        nombre_completo=nombre_completo,
        rol=rol,
        email=email,
        password_hash=hash_password(password),
        matricula=matricula,
        especialidades=spec,
    )
    db.add(user)
    db.flush()
    return user


def update_user(db: Session, usuario_id: uuid.UUID, changes: dict) -> User:
    """Update ONLY the fields sent. The password is hashed; the specialties are resolved."""
    user = get_user(db, usuario_id)

    if user.rol != Role.MEDICO and (
        changes.get("especialidades") or changes.get("matricula") is not None
    ):
        raise DoctorOnlyData()

    if changes.get("email") is not None and _email_in_use(
        db, changes["email"], exclude_id=usuario_id
    ):
        raise DuplicateEmail()

    if "especialidades" in changes:
        user.especialidades = resolve_specialties(db, changes["especialidades"] or [])
    if changes.get("password") is not None:
        user.password_hash = hash_password(changes["password"])
    for field in ("nombre_completo", "email", "matricula", "activo"):
        if field in changes:
            setattr(user, field, changes[field])

    db.flush()
    return user


def erase_user(
    db: Session,
    usuario_id: uuid.UUID,
    *,
    requested_by_id: uuid.UUID,
    now: datetime | None = None,
) -> tuple[str, int]:
    """Erase a staff member's personal data for good. Flush, no commit.

    For someone who has left: deactivating would keep them in the list as if they were coming
    back. Same two outcomes as with a patient, because appointments point at whoever attended
    and whoever booked them:

    - no appointments  -> the row is deleted;
    - with appointments -> name, email, password and licence number are wiped, so the past
      appointments keep their shape while the person is no longer identifiable.

    Either way the schedule and the specialties go: someone who left holds neither.
    Returns what happened and how many appointments were kept.
    """
    user = get_user(db, usuario_id)
    if user.id == requested_by_id:
        raise CannotEraseSelf()

    now = now or now_center()
    upcoming = (
        db.query(Appointment)
        .filter(Appointment.medico_id == usuario_id)
        .filter(Appointment.estado.in_(ACTIVE_STATUSES))
        .filter(Appointment.starts_at >= now)
        .count()
    )
    if upcoming:
        raise UserHasUpcomingAppointments(upcoming)

    db.query(Availability).filter(Availability.usuario_id == usuario_id).delete()
    user.especialidades = []
    db.flush()

    history = (
        db.query(Appointment)
        .filter(
            or_(
                Appointment.medico_id == usuario_id,
                Appointment.creado_por_id == usuario_id,
            )
        )
        .count()
    )
    if history == 0:
        db.delete(user)
        db.flush()
        return "eliminado", 0

    user.nombre_completo = ERASED_NAME
    user.email = None
    user.password_hash = None
    user.matricula = None
    user.activo = False
    db.flush()
    return "anonimizado", history
