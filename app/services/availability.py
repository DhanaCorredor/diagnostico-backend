"""Lógica de disponibilidad: ver y definir las franjas horarias semanales de un médico."""

import uuid
from datetime import time

from sqlalchemy.orm import Session

from app.enums import Role
from app.models import Availability, User


class DoctorNotFound(Exception):
    """El médico indicado no existe o no tiene rol MEDICO."""


class InvalidSlot(Exception):
    """La franja no es válida: la hora de inicio no es anterior a la de fin."""


class OverlappingSlot(Exception):
    """La franja se cruza con otra ya definida para ese médico ese mismo día."""


def list_availability(db: Session, medico_id: uuid.UUID) -> list[Availability]:
    """Franjas de un médico, ordenadas por día de la semana y hora de inicio."""
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
    """True si el médico ya tiene ese día una franja cruzada con este horario.

    Misma regla que en las citas: las franjas pegadas (08:00-12:00 y 12:00-16:00) no se cruzan.
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
    """Crea una franja de un médico validando médico, inicio < fin y que no se cruce con otra.

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
