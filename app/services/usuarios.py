"""Lógica de gestión del personal que hace login (ADMIN/RECEPCION/MEDICO): CRUD, solo ADMIN."""

import uuid

from sqlalchemy.orm import Session, selectinload

from app.auth import hashear_password
from app.enums import Role
from app.models import Specialty, User
from app.services.comun import valor_en_uso

ROLES_STAFF = (Role.ADMIN, Role.RECEPCION, Role.MEDICO)


class UsuarioNoEncontrado(Exception):
    """No existe un usuario de personal con ese id."""


class EmailDuplicado(Exception):
    """El email ya lo usa otro usuario."""


class RolNoPermitido(Exception):
    """El rol indicado no se puede crear aquí (p. ej. PACIENTE)."""


class EspecialidadNoEncontrada(Exception):
    """Alguna de las especialidades indicadas no existe."""


class DatosSoloDeMedico(Exception):
    """Se han indicado especialidades o matrícula para un usuario que no es médico."""


def _email_en_uso(db: Session, email: str, excluir_id: uuid.UUID | None = None) -> bool:
    return valor_en_uso(db, User, User.email, email, excluir_id)


def _resolver_especialidades(db: Session, ids: list[uuid.UUID]) -> list[Specialty]:
    """Convierte una lista de ids en objetos Especialidad; lanza si alguno no existe."""
    if not ids:
        return []
    encontradas = db.query(Specialty).filter(Specialty.id.in_(ids)).all()
    if len(encontradas) != len(set(ids)):
        raise EspecialidadNoEncontrada()
    return encontradas


def listar_personal(db: Session) -> list[User]:
    """Devuelve el personal (todo menos pacientes), ordenado por nombre."""
    return (
        db.query(User)
        .options(selectinload(User.especialidades))
        .filter(User.rol != Role.PACIENTE)
        .order_by(User.nombre_completo)
        .all()
    )


def obtener_usuario(db: Session, usuario_id: uuid.UUID) -> User:
    """Devuelve un usuario de personal por id, o lanza UsuarioNoEncontrado."""
    usuario = db.get(User, usuario_id)
    if usuario is None or usuario.rol == Role.PACIENTE:
        raise UsuarioNoEncontrado()
    return usuario


def crear_usuario(
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
        raise RolNoPermitido()
    if rol != Role.MEDICO and (especialidades or matricula is not None):
        raise DatosSoloDeMedico()
    if _email_en_uso(db, email):
        raise EmailDuplicado()
    esp = _resolver_especialidades(db, especialidades)

    usuario = User(
        nombre_completo=nombre_completo,
        rol=rol,
        email=email,
        password_hash=hashear_password(password),
        matricula=matricula,
        especialidades=esp,
    )
    db.add(usuario)
    db.flush()
    return usuario


def actualizar_usuario(db: Session, usuario_id: uuid.UUID, cambios: dict) -> User:
    """Actualiza SOLO los campos enviados. La contraseña se hashea; especialidades se resuelven."""
    usuario = obtener_usuario(db, usuario_id)

    if usuario.rol != Role.MEDICO and (
        cambios.get("especialidades") or cambios.get("matricula") is not None
    ):
        raise DatosSoloDeMedico()

    if cambios.get("email") is not None and _email_en_uso(
        db, cambios["email"], excluir_id=usuario_id
    ):
        raise EmailDuplicado()

    if "especialidades" in cambios:
        usuario.especialidades = _resolver_especialidades(db, cambios["especialidades"] or [])
    if cambios.get("password") is not None:
        usuario.password_hash = hashear_password(cambios["password"])
    for campo in ("nombre_completo", "email", "matricula", "activo"):
        if campo in cambios:
            setattr(usuario, campo, cambios[campo])

    db.flush()
    return usuario


def desactivar_usuario(db: Session, usuario_id: uuid.UUID) -> User:
    """Baja lógica de un usuario de personal: `activo=False`. Flush (no commit)."""
    usuario = obtener_usuario(db, usuario_id)
    usuario.activo = False
    db.flush()
    return usuario
