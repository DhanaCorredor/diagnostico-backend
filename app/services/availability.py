"""Availability logic: view and define the weekly time slots of a doctor."""

import uuid
from datetime import time

from sqlalchemy.orm import Session

from app.enums import Role
from app.models import Availability, User


class DoctorNotFound(Exception):
    """The given doctor does not exist or does not have the MEDICO role."""


class InvalidSlot(Exception):
    """The slot is not valid: the start time is not earlier than the end time."""


class OverlappingSlot(Exception):
    """The slot overlaps another one already defined for that doctor on that same day."""


def list_availability(db: Session, medico_id: uuid.UUID) -> list[Availability]:
    """Slots of a doctor, ordered by day of the week and start time."""
    return (
        db.query(Availability)
        .filter(Availability.usuario_id == medico_id)
        .order_by(Availability.dia_semana, Availability.hora_inicio)
        .all()
    )


def has_overlapping_slot(
    db: Session,
    medico_id: uuid.UUID,
    dia_semana: int,
    hora_inicio: time,
    hora_fin: time,
) -> bool:
    """True if the doctor already has a slot on that day overlapping this time range.

    Same rule as for appointments: adjacent slots (08:00-12:00 and 12:00-16:00) do not overlap.
    """
    q = (
        db.query(Availability)
        .filter(Availability.usuario_id == medico_id)
        .filter(Availability.dia_semana == dia_semana)
        .filter(Availability.hora_inicio < hora_fin)
        .filter(Availability.hora_fin > hora_inicio)
    )
    return db.query(q.exists()).scalar()


def create_availability(
    db: Session,
    *,
    medico_id: uuid.UUID,
    dia_semana: int,
    hora_inicio: time,
    hora_fin: time,
) -> Availability:
    """Create a slot for a doctor, validating the doctor, start < end and that it does not overlap.

    Flush, no commit.
    """
    doctor = db.get(User, medico_id)
    if doctor is None or doctor.rol != Role.MEDICO:
        raise DoctorNotFound()
    if hora_inicio >= hora_fin:
        raise InvalidSlot()
    if has_overlapping_slot(db, medico_id, dia_semana, hora_inicio, hora_fin):
        raise OverlappingSlot()

    slot = Availability(
        usuario_id=medico_id,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
    )
    db.add(slot)
    db.flush()
    return slot
