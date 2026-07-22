"""Catálogo de servicios, especialidades y médicos.

Incluye las lecturas que alimentan los desplegables del frontend (elegir
servicio, especialidad o médico al agendar) y la gestión de catálogos del ADMIN
(alta/edición de servicios y alta de especialidades). Vive en la capa de
servicio para poder probarlo sin levantar la API.
"""

import uuid

from sqlalchemy.orm import Session, selectinload

from app.models import Especialidad, Rol, Servicio, ServicioCategoria, Usuario


class ServicioNoEncontrado(Exception):
    """No existe un servicio con ese id."""


class NombreDuplicado(Exception):
    """Ya existe un servicio o especialidad con ese nombre (el nombre es único)."""


def listar_servicios(db: Session) -> list[Servicio]:
    """Devuelve los servicios activos del catálogo, ordenados por nombre."""
    return (
        db.query(Servicio)
        .filter(Servicio.activo.is_(True))
        .order_by(Servicio.nombre)
        .all()
    )


def listar_medicos(db: Session) -> list[Usuario]:
    """Devuelve los médicos activos, ordenados por nombre, con sus especialidades."""
    return (
        db.query(Usuario)
        .options(selectinload(Usuario.especialidades))  # evita N+1 al serializar
        .filter(Usuario.rol == Rol.MEDICO)
        .filter(Usuario.activo.is_(True))
        .order_by(Usuario.nombre_completo)
        .all()
    )


def listar_especialidades(db: Session) -> list[Especialidad]:
    """Devuelve todas las especialidades del catálogo, ordenadas por nombre."""
    return db.query(Especialidad).order_by(Especialidad.nombre).all()


# --- Gestión de catálogos (ADMIN) -------------------------------------------


def _servicio_nombre_en_uso(
    db: Session, nombre: str, excluir_id: uuid.UUID | None = None
) -> bool:
    """True si ya hay un servicio con ese nombre (excluyendo, si se indica, uno propio)."""
    q = db.query(Servicio).filter(Servicio.nombre == nombre)
    if excluir_id is not None:
        q = q.filter(Servicio.id != excluir_id)
    return db.query(q.exists()).scalar()


def crear_servicio(
    db: Session, *, nombre: str, categoria: ServicioCategoria
) -> Servicio:
    """Da de alta un servicio en el catálogo. Nombre único. Flush (no commit)."""
    if _servicio_nombre_en_uso(db, nombre):
        raise NombreDuplicado()
    servicio = Servicio(nombre=nombre, categoria=categoria)
    db.add(servicio)
    db.flush()
    return servicio


def actualizar_servicio(db: Session, servicio_id: uuid.UUID, cambios: dict) -> Servicio:
    """Edita SOLO los campos enviados de un servicio (nombre, categoría, activo).

    Permite desactivar un servicio (`activo=False`) sin borrarlo. Flush (no commit).
    """
    servicio = db.get(Servicio, servicio_id)
    if servicio is None:
        raise ServicioNoEncontrado()
    if cambios.get("nombre") is not None and _servicio_nombre_en_uso(
        db, cambios["nombre"], excluir_id=servicio_id
    ):
        raise NombreDuplicado()
    for campo in ("nombre", "categoria", "activo"):
        if campo in cambios:
            setattr(servicio, campo, cambios[campo])
    db.flush()
    return servicio


def crear_especialidad(db: Session, *, nombre: str) -> Especialidad:
    """Da de alta una especialidad en el catálogo. Nombre único. Flush (no commit)."""
    existe = db.query(
        db.query(Especialidad).filter(Especialidad.nombre == nombre).exists()
    ).scalar()
    if existe:
        raise NombreDuplicado()
    especialidad = Especialidad(nombre=nombre)
    db.add(especialidad)
    db.flush()
    return especialidad
