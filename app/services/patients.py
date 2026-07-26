"""Lógica de negocio de pacientes: upsert al agendar + listar/ver/editar/dar de baja."""

import uuid

from sqlalchemy.orm import Session

from app.enums import Role
from app.models import User
from app.services.common import value_in_use


class AmbiguousPatients(Exception):
    """Varios pacientes coinciden; recepción debe elegir. Lleva la lista de candidatos."""

    def __init__(self, candidates):
        self.candidates = candidates
        super().__init__(f"{len(candidates)} pacientes coinciden; recepción debe elegir")


def find_or_create_patient(db: Session, nombre_completo: str, edad: int) -> User:
    """Busca un paciente por nombre_completo + edad y lo devuelve; si no existe, lo crea.

    Lanza AmbiguousPatients si coinciden varios (recepción debe elegir). Flush, no commit.
    """
    matches = (
        db.query(User)
        .filter(User.rol == Role.PACIENTE)
        .filter(User.activo.is_(True))
        .filter(User.nombre_completo == nombre_completo)
        .filter(User.edad == edad)
        .all()
    )
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise AmbiguousPatients(matches)

    patient = User(nombre_completo=nombre_completo, edad=edad, rol=Role.PACIENTE)
    db.add(patient)
    db.flush()
    return patient


class PatientNotFound(Exception):
    """No existe un paciente con ese id."""


class DuplicateNationalId(Exception):
    """La cédula indicada ya pertenece a otra persona."""


def _national_id_in_use(db: Session, cedula: str, exclude_id: uuid.UUID | None = None) -> bool:
    """True si la cédula ya pertenece a otra persona (excluyendo, si se indica, un id)."""
    return value_in_use(db, User, User.cedula, cedula, exclude_id)


def list_patients(db: Session) -> list[User]:
    """Devuelve los pacientes activos, ordenados por nombre."""
    return (
        db.query(User)
        .filter(User.rol == Role.PACIENTE)
        .filter(User.activo.is_(True))
        .order_by(User.nombre_completo)
        .all()
    )


def get_patient(db: Session, paciente_id: uuid.UUID) -> User:
    """Devuelve un paciente por id, o lanza PatientNotFound."""
    patient = db.get(User, paciente_id)
    if patient is None or patient.rol != Role.PACIENTE:
        raise PatientNotFound()
    return patient


def create_patient(db: Session, data: dict) -> User:
    """Da de alta un paciente manualmente, sin deduplicar (cédula única si se indica). Flush, no commit."""
    cedula = data.get("cedula")
    if cedula is not None and _national_id_in_use(db, cedula):
        raise DuplicateNationalId()

    patient = User(rol=Role.PACIENTE, **data)
    db.add(patient)
    db.flush()
    return patient


def update_patient(db: Session, paciente_id: uuid.UUID, changes: dict) -> User:
    """Actualiza solo los campos presentes en `changes` (cédula única si se cambia). Flush, no commit."""
    patient = get_patient(db, paciente_id)

    new_national_id = changes.get("cedula")
    if new_national_id is not None and _national_id_in_use(db, new_national_id, exclude_id=paciente_id):
        raise DuplicateNationalId()

    for field, value in changes.items():
        setattr(patient, field, value)
    db.flush()
    return patient


def deactivate_patient(db: Session, paciente_id: uuid.UUID) -> User:
    """Da de baja (lógica) a un paciente: `activo=False`. Hace flush (no commit)."""
    patient = get_patient(db, paciente_id)
    patient.activo = False
    db.flush()
    return patient
