"""Patient business logic: upsert when scheduling + list/view/edit/erase."""

import uuid

from sqlalchemy.orm import Session

from app.enums import Role
from app.models import Appointment, User
from app.services.common import value_in_use

ERASED_NAME = "Paciente eliminado"


class AmbiguousPatients(Exception):
    """Several patients match; reception must choose. Carries the list of candidates."""

    def __init__(self, candidates):
        self.candidates = candidates
        super().__init__(f"{len(candidates)} pacientes coinciden; recepción debe elegir")


def find_or_create_patient(db: Session, nombre_completo: str, edad: int) -> User:
    """Look up a patient by nombre_completo + edad and return it; create it if it does not exist.

    Raises AmbiguousPatients if several match (reception must choose). Flush, no commit.
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
    """There is no patient with that id."""


class DuplicateNationalId(Exception):
    """The given national id already belongs to another person."""


def _national_id_in_use(db: Session, cedula: str, exclude_id: uuid.UUID | None = None) -> bool:
    """True if the national id already belongs to another person (optionally excluding an id)."""
    return value_in_use(db, User, User.cedula, cedula, exclude_id)


def list_patients(db: Session) -> list[User]:
    """Return the active patients, ordered by name."""
    return (
        db.query(User)
        .filter(User.rol == Role.PACIENTE)
        .filter(User.activo.is_(True))
        .order_by(User.nombre_completo)
        .all()
    )


def get_patient(db: Session, paciente_id: uuid.UUID) -> User:
    """Return a patient by id, or raise PatientNotFound."""
    patient = db.get(User, paciente_id)
    if patient is None or patient.rol != Role.PACIENTE:
        raise PatientNotFound()
    return patient


def create_patient(db: Session, data: dict) -> User:
    """Register a patient manually, without deduplicating (unique national id if given). Flush, no commit."""
    cedula = data.get("cedula")
    if cedula is not None and _national_id_in_use(db, cedula):
        raise DuplicateNationalId()

    patient = User(rol=Role.PACIENTE, **data)
    db.add(patient)
    db.flush()
    return patient


def update_patient(db: Session, paciente_id: uuid.UUID, changes: dict) -> User:
    """Update only the fields present in `changes` (unique national id if changed). Flush, no commit."""
    patient = get_patient(db, paciente_id)

    new_national_id = changes.get("cedula")
    if new_national_id is not None and _national_id_in_use(db, new_national_id, exclude_id=paciente_id):
        raise DuplicateNationalId()

    for field, value in changes.items():
        setattr(patient, field, value)
    db.flush()
    return patient


def erase_patient(db: Session, paciente_id: uuid.UUID) -> tuple[str, int]:
    """Erase a patient's personal data for good. Flush, no commit.

    Appointments only store `paciente_id`, so the row has to survive for past appointments to
    keep making sense. Hence two outcomes, both leaving no personal data behind:

    - no appointments  -> the row is deleted, nothing is left;
    - with appointments -> name, national id, phone, birth date and age are wiped and the patient
      leaves the list, while its appointments stay as an unidentified record of the visit.

    Returns what happened and how many appointments were kept.
    """
    patient = get_patient(db, paciente_id)
    appointments = (
        db.query(Appointment).filter(Appointment.paciente_id == paciente_id).count()
    )

    if appointments == 0:
        db.delete(patient)
        db.flush()
        return "eliminado", 0

    patient.nombre_completo = ERASED_NAME
    patient.cedula = None
    patient.telefono = None
    patient.fecha_nacimiento = None
    patient.edad = None
    patient.alergias = None
    patient.antecedentes = None
    patient.activo = False
    db.flush()
    return "anonimizado", appointments
