"""Catálogo de servicios, especialidades y médicos: lecturas para los desplegables y gestión del ADMIN."""

import uuid

from sqlalchemy.orm import Session, selectinload

from app.enums import Role, ServiceCategory
from app.models import Especialidad, Servicio, Usuario
from app.services.comun import valor_en_uso


class ServicioNoEncontrado(Exception):
    """No existe un servicio con ese id."""


class NombreDuplicado(Exception):
    """Ya existe un servicio o especialidad con ese nombre (el nombre es único)."""


def listar_servicios(
    db: Session, medico_id: uuid.UUID | None = None
) -> list[Servicio]:
    """Devuelve los servicios activos ordenados por nombre; con `medico_id`, solo los de sus especialidades."""
    consulta = (
        db.query(Servicio)
        .options(selectinload(Servicio.especialidades))
        .filter(Servicio.activo.is_(True))
    )
    if medico_id is not None:
        consulta = consulta.filter(
            Servicio.especialidades.any(Especialidad.medicos.any(Usuario.id == medico_id))
        )
    return consulta.order_by(Servicio.nombre).all()


def listar_medicos(db: Session) -> list[Usuario]:
    """Devuelve los médicos activos, ordenados por nombre, con sus especialidades."""
    return (
        db.query(Usuario)
        .options(selectinload(Usuario.especialidades))
        .filter(Usuario.rol == Role.MEDICO)
        .filter(Usuario.activo.is_(True))
        .order_by(Usuario.nombre_completo)
        .all()
    )


def listar_especialidades(db: Session) -> list[Especialidad]:
    """Devuelve todas las especialidades del catálogo, ordenadas por nombre."""
    return db.query(Especialidad).order_by(Especialidad.nombre).all()


def _servicio_nombre_en_uso(
    db: Session, nombre: str, excluir_id: uuid.UUID | None = None
) -> bool:
    """True si ya hay un servicio con ese nombre (excluyendo, si se indica, uno propio)."""
    return valor_en_uso(db, Servicio, Servicio.nombre, nombre, excluir_id)


def crear_servicio(
    db: Session, *, nombre: str, categoria: ServiceCategory
) -> Servicio:
    """Da de alta un servicio en el catálogo. Nombre único. Flush (no commit)."""
    if _servicio_nombre_en_uso(db, nombre):
        raise NombreDuplicado()
    servicio = Servicio(nombre=nombre, categoria=categoria)
    db.add(servicio)
    db.flush()
    return servicio


def actualizar_servicio(db: Session, servicio_id: uuid.UUID, cambios: dict) -> Servicio:
    """Edita solo los campos enviados de un servicio; permite desactivarlo (`activo=False`). Flush, no commit."""
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
    if valor_en_uso(db, Especialidad, Especialidad.nombre, nombre):
        raise NombreDuplicado()
    especialidad = Especialidad(nombre=nombre)
    db.add(especialidad)
    db.flush()
    return especialidad
