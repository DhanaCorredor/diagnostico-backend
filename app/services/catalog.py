"""Catálogo de servicios, especialidades y médicos: lecturas para los desplegables y gestión del ADMIN."""

import uuid

from sqlalchemy.orm import Session, selectinload

from app.enums import Role, ServiceCategory
from app.models import Specialty, Service, User
from app.services.common import value_in_use


class ServiceNotFound(Exception):
    """No existe un servicio con ese id."""


class DuplicateName(Exception):
    """Ya existe un servicio o especialidad con ese nombre (el nombre es único)."""


def list_services(
    db: Session, medico_id: uuid.UUID | None = None
) -> list[Service]:
    """Devuelve los servicios activos ordenados por nombre; con `medico_id`, solo los de sus especialidades."""
    consulta = (
        db.query(Service)
        .options(selectinload(Service.especialidades))
        .filter(Service.activo.is_(True))
    )
    if medico_id is not None:
        consulta = consulta.filter(
            Service.especialidades.any(Specialty.medicos.any(User.id == medico_id))
        )
    return consulta.order_by(Service.nombre).all()


def list_doctors(db: Session) -> list[User]:
    """Devuelve los médicos activos, ordenados por nombre, con sus especialidades."""
    return (
        db.query(User)
        .options(selectinload(User.especialidades))
        .filter(User.rol == Role.MEDICO)
        .filter(User.activo.is_(True))
        .order_by(User.nombre_completo)
        .all()
    )


def list_specialties(db: Session) -> list[Specialty]:
    """Devuelve todas las especialidades del catálogo, ordenadas por nombre."""
    return db.query(Specialty).order_by(Specialty.nombre).all()


def _service_name_in_use(
    db: Session, nombre: str, excluir_id: uuid.UUID | None = None
) -> bool:
    """True si ya hay un servicio con ese nombre (excluyendo, si se indica, uno propio)."""
    return value_in_use(db, Service, Service.nombre, nombre, excluir_id)


def create_service(
    db: Session, *, nombre: str, categoria: ServiceCategory
) -> Service:
    """Da de alta un servicio en el catálogo. Nombre único. Flush (no commit)."""
    if _service_name_in_use(db, nombre):
        raise DuplicateName()
    service = Service(nombre=nombre, categoria=categoria)
    db.add(service)
    db.flush()
    return service


def update_service(db: Session, servicio_id: uuid.UUID, cambios: dict) -> Service:
    """Edita solo los campos enviados de un servicio; permite desactivarlo (`activo=False`). Flush, no commit."""
    service = db.get(Service, servicio_id)
    if service is None:
        raise ServiceNotFound()
    if cambios.get("nombre") is not None and _service_name_in_use(
        db, cambios["nombre"], excluir_id=servicio_id
    ):
        raise DuplicateName()
    for campo in ("nombre", "categoria", "activo"):
        if campo in cambios:
            setattr(service, campo, cambios[campo])
    db.flush()
    return service


def create_specialty(db: Session, *, nombre: str) -> Specialty:
    """Da de alta una especialidad en el catálogo. Nombre único. Flush (no commit)."""
    if value_in_use(db, Specialty, Specialty.nombre, nombre):
        raise DuplicateName()
    especialidad = Specialty(nombre=nombre)
    db.add(especialidad)
    db.flush()
    return especialidad
