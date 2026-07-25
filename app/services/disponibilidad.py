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


def list_availability(db: Session, medico_id: uuid.UUID) -> list[Availability]:
    """Franjas de un médico, ordenadas por día de la semana y hora de inicio."""
    return (
        db.query(Availability)
        .filter(Availability.usuario_id == medico_id)
        .order_by(Availability.dia_semana, Availability.hora_inicio)
        .all()
    )


def create_availability(
    db: Session,
    *,
    medico_id: uuid.UUID,
    dia_semana: int,
    hora_inicio: time,
    hora_fin: time,
) -> Availability:
    """Crea una franja para un médico, validando el médico y que inicio < fin. Flush, no commit."""
    doctor = db.get(User, medico_id)
    if doctor is None or doctor.rol != Role.MEDICO:
        raise DoctorNotFound()
    if hora_inicio >= hora_fin:
        raise InvalidSlot()

    slot = Availability(
        usuario_id=medico_id,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
    )
    db.add(slot)
    db.flush()
    return slot
