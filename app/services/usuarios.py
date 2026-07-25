"""Lógica de gestión del personal que hace login (ADMIN/RECEPCION/MEDICO): CRUD, solo ADMIN."""

import uuid

from sqlalchemy.orm import Session, selectinload

from app.auth import hash_password
from app.enums import Role
from app.models import Specialty, User
from app.services.comun import value_in_use

ROLES_STAFF = (Role.ADMIN, Role.RECEPCION, Role.MEDICO)


class UserNotFound(Exception):
    """No existe un usuario de personal con ese id."""


class DuplicateEmail(Exception):
    """El email ya lo usa otro usuario."""


class RoleNotAllowed(Exception):
    """El rol indicado no se puede crear aquí (p. ej. PACIENTE)."""


class SpecialtyNotFound(Exception):
    """Alguna de las especialidades indicadas no existe."""


class DoctorOnlyData(Exception):
    """Se han indicado especialidades o matrícula para un usuario que no es médico."""


def _email_in_use(db: Session, email: str, excluir_id: uuid.UUID | None = None) -> bool:
    return value_in_use(db, User, User.email, email, excluir_id)


def _resolve_specialties(db: Session, ids: list[uuid.UUID]) -> list[Specialty]:
    """Convierte una lista de ids en objetos Especialidad; lanza si alguno no existe."""
    if not ids:
        return []
    encontradas = db.query(Specialty).filter(Specialty.id.in_(ids)).all()
    if len(encontradas) != len(set(ids)):
        raise SpecialtyNotFound()
    return encontradas


def list_staff(db: Session) -> list[User]:
    """Devuelve el personal (todo menos pacientes), ordenado por nombre."""
    return (
        db.query(User)
        .options(selectinload(User.especialidades))
        .filter(User.rol != Role.PACIENTE)
        .order_by(User.nombre_completo)
        .all()
    )


def get_user(db: Session, usuario_id: uuid.UUID) -> User:
    """Devuelve un usuario de personal por id, o lanza UsuarioNoEncontrado."""
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
    """Crea un usuario de personal. Valida rol y email, hashea la contraseña. Flush (no commit)."""
    if rol not in ROLES_STAFF:
        raise RoleNotAllowed()
    if rol != Role.MEDICO and (especialidades or matricula is not None):
        raise DoctorOnlyData()
    if _email_in_use(db, email):
        raise DuplicateEmail()
    esp = _resolve_specialties(db, especialidades)

    user = User(
        nombre_completo=nombre_completo,
        rol=rol,
        email=email,
        password_hash=hash_password(password),
        matricula=matricula,
        especialidades=esp,
    )
    db.add(user)
    db.flush()
    return user


def update_user(db: Session, usuario_id: uuid.UUID, cambios: dict) -> User:
    """Actualiza SOLO los campos enviados. La contraseña se hashea; especialidades se resuelven."""
    user = get_user(db, usuario_id)

    if user.rol != Role.MEDICO and (
        cambios.get("especialidades") or cambios.get("matricula") is not None
    ):
        raise DoctorOnlyData()

    if cambios.get("email") is not None and _email_in_use(
        db, cambios["email"], excluir_id=usuario_id
    ):
        raise DuplicateEmail()

    if "especialidades" in cambios:
        user.especialidades = _resolve_specialties(db, cambios["especialidades"] or [])
    if cambios.get("password") is not None:
        user.password_hash = hash_password(cambios["password"])
    for campo in ("nombre_completo", "email", "matricula", "activo"):
        if campo in cambios:
            setattr(user, campo, cambios[campo])

    db.flush()
    return user


def deactivate_user(db: Session, usuario_id: uuid.UUID) -> User:
    """Baja lógica de un usuario de personal: `activo=False`. Flush (no commit)."""
    user = get_user(db, usuario_id)
    user.activo = False
    db.flush()
    return user
