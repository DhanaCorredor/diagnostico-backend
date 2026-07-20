"""Lógica de negocio de la gestión de personal/médicos (CRUD, solo ADMIN).

Gestiona los usuarios que hacen login (ADMIN, RECEPCION, MEDICO): alta, edición,
hash de contraseña y asignación de especialidades (N:M) a los médicos. Los
pacientes NO se gestionan aquí (entran por el upsert al agendar).
"""

import uuid

from sqlalchemy.orm import Session

from app.auth import hashear_password
from app.models import Especialidad, Rol, Usuario

# Roles de personal que hacen login (nunca PACIENTE).
ROLES_STAFF = (Rol.ADMIN, Rol.RECEPCION, Rol.MEDICO)


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
    q = db.query(Usuario).filter(Usuario.email == email)
    if excluir_id is not None:
        q = q.filter(Usuario.id != excluir_id)
    return db.query(q.exists()).scalar()


def _resolver_especialidades(db: Session, ids: list[uuid.UUID]) -> list[Especialidad]:
    """Convierte una lista de ids en objetos Especialidad; lanza si alguno no existe."""
    if not ids:
        return []
    encontradas = db.query(Especialidad).filter(Especialidad.id.in_(ids)).all()
    if len(encontradas) != len(set(ids)):
        raise EspecialidadNoEncontrada()
    return encontradas


def listar_personal(db: Session) -> list[Usuario]:
    """Devuelve el personal (todo menos pacientes), ordenado por nombre."""
    return (
        db.query(Usuario)
        .filter(Usuario.rol != Rol.PACIENTE)
        .order_by(Usuario.nombre_completo)
        .all()
    )


def obtener_usuario(db: Session, usuario_id: uuid.UUID) -> Usuario:
    """Devuelve un usuario de personal por id, o lanza UsuarioNoEncontrado."""
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or usuario.rol == Rol.PACIENTE:
        raise UsuarioNoEncontrado()
    return usuario


def crear_usuario(
    db: Session,
    *,
    nombre_completo: str,
    rol: Rol,
    email: str,
    password: str,
    matricula: str | None,
    especialidades: list[uuid.UUID],
) -> Usuario:
    """Crea un usuario de personal. Valida rol y email, hashea la contraseña. Flush (no commit)."""
    if rol not in ROLES_STAFF:
        raise RolNoPermitido()
    if rol != Rol.MEDICO and (especialidades or matricula is not None):
        raise DatosSoloDeMedico()  # especialidades y matrícula solo para médicos
    if _email_en_uso(db, email):
        raise EmailDuplicado()
    esp = _resolver_especialidades(db, especialidades)

    usuario = Usuario(
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


def actualizar_usuario(db: Session, usuario_id: uuid.UUID, cambios: dict) -> Usuario:
    """Actualiza SOLO los campos enviados. La contraseña se hashea; especialidades se resuelven."""
    usuario = obtener_usuario(db, usuario_id)

    if usuario.rol != Rol.MEDICO and (
        cambios.get("especialidades") or cambios.get("matricula") is not None
    ):
        raise DatosSoloDeMedico()  # especialidades y matrícula solo para médicos

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


def desactivar_usuario(db: Session, usuario_id: uuid.UUID) -> Usuario:
    """Baja lógica de un usuario de personal: `activo=False`. Flush (no commit)."""
    usuario = obtener_usuario(db, usuario_id)
    usuario.activo = False
    db.flush()
    return usuario
