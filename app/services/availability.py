"""Availability logic: view, define, edit and remove the weekly time slots of a doctor."""

import uuid
from datetime import datetime, time

from sqlalchemy.orm import Session

from app.enums import AppointmentStatus, Role
from app.models import Appointment, Availability, User
from app.services.appointments import now_center

ACTIVE_STATUSES = (AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED)


class DoctorNotFound(Exception):
    """The given doctor does not exist or does not have the MEDICO role."""


class InvalidSlot(Exception):
    """The slot is not valid: the start time is not earlier than the end time."""


class OverlappingSlot(Exception):
    """The slot overlaps another one already defined for that doctor on that same day."""


class SlotNotFound(Exception):
    """There is no availability slot with that id."""


class StrandedAppointments(Exception):
    """Removing or shrinking the slot would leave booked appointments outside working hours."""

    def __init__(self, count):
        self.count = count
        super().__init__(f"{count} booked appointments would be left outside working hours")


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
    exclude_slot_id: uuid.UUID | None = None,
) -> bool:
    """True if the doctor already has a slot on that day overlapping this time range.

    Same rule as for appointments: adjacent slots (08:00-12:00 and 12:00-16:00) do not overlap.
    `exclude_slot_id` skips one slot (when editing, so it does not clash with itself).
    """
    q = (
        db.query(Availability)
        .filter(Availability.usuario_id == medico_id)
        .filter(Availability.dia_semana == dia_semana)
        .filter(Availability.hora_inicio < hora_fin)
        .filter(Availability.hora_fin > hora_inicio)
    )
    if exclude_slot_id is not None:
        q = q.filter(Availability.id != exclude_slot_id)
    return db.query(q.exists()).scalar()


def _covered_appointments(
    db: Session,
    medico_id: uuid.UUID,
    dia_semana: int,
    hora_inicio: time,
    hora_fin: time,
    now: datetime,
) -> list[Appointment]:
    """Active appointments still to come that fall inside that weekday and time range.

    Since two slots of the same doctor cannot overlap on the same day, an appointment is
    covered by at most one slot, so this list is exactly what that slot is holding up.
    """
    upcoming = (
        db.query(Appointment)
        .filter(Appointment.medico_id == medico_id)
        .filter(Appointment.estado.in_(ACTIVE_STATUSES))
        .filter(Appointment.starts_at >= now)
        .all()
    )
    return [
        a
        for a in upcoming
        if (a.starts_at.weekday() + 1) % 7 == dia_semana
        and hora_inicio <= a.starts_at.time()
        and a.ends_at.time() <= hora_fin
    ]


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


def update_availability(
    db: Session,
    *,
    franja_id: uuid.UUID,
    dia_semana: int | None = None,
    hora_inicio: time | None = None,
    hora_fin: time | None = None,
    now: datetime | None = None,
) -> Availability:
    """Edit a slot (partial: fields set to None are left unchanged). Flush, no commit.

    The doctor is never changed. Besides start < end and not overlapping another slot, the new
    range must still cover every appointment the old one was holding: shrinking a slot cannot
    strand a booked appointment outside the doctor's working hours.
    """
    slot = db.get(Availability, franja_id)
    if slot is None:
        raise SlotNotFound()

    new_day = dia_semana if dia_semana is not None else slot.dia_semana
    new_start = hora_inicio if hora_inicio is not None else slot.hora_inicio
    new_end = hora_fin if hora_fin is not None else slot.hora_fin

    if new_start >= new_end:
        raise InvalidSlot()
    if has_overlapping_slot(
        db, slot.usuario_id, new_day, new_start, new_end, exclude_slot_id=slot.id
    ):
        raise OverlappingSlot()

    now = now or now_center()
    covered = _covered_appointments(
        db, slot.usuario_id, slot.dia_semana, slot.hora_inicio, slot.hora_fin, now
    )
    stranded = [
        a
        for a in covered
        if not (
            (a.starts_at.weekday() + 1) % 7 == new_day
            and new_start <= a.starts_at.time()
            and a.ends_at.time() <= new_end
        )
    ]
    if stranded:
        raise StrandedAppointments(len(stranded))

    slot.dia_semana = new_day
    slot.hora_inicio = new_start
    slot.hora_fin = new_end
    db.flush()
    return slot


def delete_availability(
    db: Session, franja_id: uuid.UUID, now: datetime | None = None
) -> None:
    """Remove a slot, unless it is still holding up booked appointments. Flush, no commit."""
    slot = db.get(Availability, franja_id)
    if slot is None:
        raise SlotNotFound()

    now = now or now_center()
    covered = _covered_appointments(
        db, slot.usuario_id, slot.dia_semana, slot.hora_inicio, slot.hora_fin, now
    )
    if covered:
        raise StrandedAppointments(len(covered))

    db.delete(slot)
    db.flush()
