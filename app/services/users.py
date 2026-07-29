"""Management logic for the staff who log in (ADMIN/RECEPCION/MEDICO): CRUD, ADMIN only."""

import uuid

from sqlalchemy.orm import Session, selectinload

from app.auth import hash_password
from app.enums import Role
from app.models import Specialty, User
from app.services.common import value_in_use

ROLES_STAFF = (Role.ADMIN, Role.RECEPCION, Role.MEDICO)


class UserNotFound(Exception):
    """There is no staff user with that id."""


class DuplicateEmail(Exception):
    """The email is already used by another user."""


class RoleNotAllowed(Exception):
    """The given role cannot be created here (e.g. PACIENTE)."""


class SpecialtyNotFound(Exception):
    """One of the given specialties does not exist."""


class DoctorOnlyData(Exception):
    """Specialties or a license number were given for a user who is not a doctor."""


def _email_in_use(db: Session, email: str, exclude_id: uuid.UUID | None = None) -> bool:
    return value_in_use(db, User, User.email, email, exclude_id)


def _resolve_specialties(db: Session, ids: list[uuid.UUID]) -> list[Specialty]:
    """Turn a list of ids into specialty objects; raises SpecialtyNotFound if any is missing."""
    if not ids:
        return []
    found = db.query(Specialty).filter(Specialty.id.in_(ids)).all()
    if len(found) != len(set(ids)):
        raise SpecialtyNotFound()
    return found


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
    spec = _resolve_specialties(db, especialidades)

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
        user.especialidades = _resolve_specialties(db, changes["especialidades"] or [])
    if changes.get("password") is not None:
        user.password_hash = hash_password(changes["password"])
    for field in ("nombre_completo", "email", "matricula", "activo"):
        if field in changes:
            setattr(user, field, changes[field])

    db.flush()
    return user


def deactivate_user(db: Session, usuario_id: uuid.UUID) -> User:
    """Soft-delete a staff user: `activo=False`. Flush (no commit)."""
    user = get_user(db, usuario_id)
    user.activo = False
    db.flush()
    return user
