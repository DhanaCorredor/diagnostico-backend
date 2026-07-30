"""Catalog of services, specialties and doctors: reads for the dropdowns and ADMIN management."""

import uuid

from sqlalchemy.orm import Session, selectinload

from app.enums import Role, ServiceCategory
from app.models import Service, Specialty, User
from app.services.common import value_in_use


class ServiceNotFound(Exception):
    """There is no service with that id."""


class SpecialtyNotFound(Exception):
    """One of the given specialties does not exist."""


class DuplicateName(Exception):
    """A service or specialty with that name already exists (the name is unique)."""


class SpecialtyInUse(Exception):
    """The specialty is still linked to doctors or services, so it cannot be removed."""

    def __init__(self, doctors: int, services: int):
        self.doctors = doctors
        self.services = services
        super().__init__(f"linked to {doctors} doctors and {services} services")


def resolve_specialties(db: Session, ids: list[uuid.UUID]) -> list[Specialty]:
    """Turn a list of ids into specialty objects; raises SpecialtyNotFound if any is missing."""
    if not ids:
        return []
    found = db.query(Specialty).filter(Specialty.id.in_(ids)).all()
    if len(found) != len(set(ids)):
        raise SpecialtyNotFound()
    return found


def list_services(
    db: Session, medico_id: uuid.UUID | None = None
) -> list[Service]:
    """Return the active services ordered by name; with `medico_id`, only those of their specialties."""
    query = (
        db.query(Service)
        .options(selectinload(Service.especialidades))
        .filter(Service.activo.is_(True))
    )
    if medico_id is not None:
        query = query.filter(
            Service.especialidades.any(Specialty.medicos.any(User.id == medico_id))
        )
    return query.order_by(Service.nombre).all()


def list_doctors(db: Session) -> list[User]:
    """Return the active doctors, ordered by name, with their specialties."""
    return (
        db.query(User)
        .options(selectinload(User.especialidades))
        .filter(User.rol == Role.MEDICO)
        .filter(User.activo.is_(True))
        .order_by(User.nombre_completo)
        .all()
    )


def list_specialties(db: Session) -> list[Specialty]:
    """Return every specialty in the catalog, ordered by name."""
    return db.query(Specialty).order_by(Specialty.nombre).all()


def _service_name_in_use(
    db: Session, nombre: str, exclude_id: uuid.UUID | None = None
) -> bool:
    """True if a service with that name already exists (optionally excluding one of its own)."""
    return value_in_use(db, Service, Service.nombre, nombre, exclude_id)


def create_service(
    db: Session, *, nombre: str, categoria: ServiceCategory
) -> Service:
    """Register a service in the catalog. Unique name. Flush (no commit)."""
    if _service_name_in_use(db, nombre):
        raise DuplicateName()
    service = Service(nombre=nombre, categoria=categoria)
    db.add(service)
    db.flush()
    return service


def update_service(db: Session, servicio_id: uuid.UUID, changes: dict) -> Service:
    """Edit only the fields sent for a service; allows deactivating it (`activo=False`). Flush, no commit."""
    service = db.get(Service, servicio_id)
    if service is None:
        raise ServiceNotFound()
    if changes.get("nombre") is not None and _service_name_in_use(
        db, changes["nombre"], exclude_id=servicio_id
    ):
        raise DuplicateName()
    if "especialidades" in changes:
        service.especialidades = resolve_specialties(db, changes["especialidades"] or [])
    for field in ("nombre", "categoria", "activo"):
        if field in changes:
            setattr(service, field, changes[field])
    db.flush()
    return service


def create_specialty(db: Session, *, nombre: str) -> Specialty:
    """Register a specialty in the catalog. Unique name. Flush (no commit)."""
    if value_in_use(db, Specialty, Specialty.nombre, nombre):
        raise DuplicateName()
    specialty = Specialty(nombre=nombre)
    db.add(specialty)
    db.flush()
    return specialty


def update_specialty(db: Session, especialidad_id: uuid.UUID, *, nombre: str) -> Specialty:
    """Rename a specialty, keeping the name unique. Flush (no commit)."""
    specialty = db.get(Specialty, especialidad_id)
    if specialty is None:
        raise SpecialtyNotFound()
    if value_in_use(db, Specialty, Specialty.nombre, nombre, exclude_id=especialidad_id):
        raise DuplicateName()
    specialty.nombre = nombre
    db.flush()
    return specialty


def delete_specialty(db: Session, especialidad_id: uuid.UUID) -> None:
    """Remove a specialty, unless doctors or services are still linked to it. Flush, no commit.

    Specialties have no `activo` column: they are a small closed catalog, so instead of a soft
    delete the removal is blocked while something depends on it.
    """
    specialty = db.get(Specialty, especialidad_id)
    if specialty is None:
        raise SpecialtyNotFound()

    doctors = (
        db.query(User)
        .filter(User.especialidades.any(Specialty.id == especialidad_id))
        .count()
    )
    services = (
        db.query(Service)
        .filter(Service.especialidades.any(Specialty.id == especialidad_id))
        .count()
    )
    if doctors or services:
        raise SpecialtyInUse(doctors, services)

    db.delete(specialty)
    db.flush()


def deactivate_service(db: Session, servicio_id: uuid.UUID) -> Service:
    """Soft-delete a service: `activo=False`. Flush (no commit).

    It is never removed for good: appointments already booked point at it, and the catalog has
    to keep explaining what they were for.
    """
    service = db.get(Service, servicio_id)
    if service is None:
        raise ServiceNotFound()
    service.activo = False
    db.flush()
    return service
