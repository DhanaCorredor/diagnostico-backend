"""Lógica de disponibilidad: ver y definir las franjas horarias semanales de un médico.

La lee el calendario para bloquear los días/horas en que el médico no atiende.
Vive en la capa de servicio para poder probarla sin levantar la API.
"""

import uuid
from datetime import time

from sqlalchemy.orm import Session

from app.models import Disponibilidad, Rol, Usuario


class MedicoNoEncontrado(Exception):
    """El médico indicado no existe o no tiene rol MEDICO."""


class FranjaInvalida(Exception):
    """La franja no es válida: la hora de inicio no es anterior a la de fin."""


def listar_disponibilidad(db: Session, medico_id: uuid.UUID) -> list[Disponibilidad]:
    """Franjas de un médico, ordenadas por día de la semana y hora de inicio."""
    return (
        db.query(Disponibilidad)
        .filter(Disponibilidad.usuario_id == medico_id)
        .order_by(Disponibilidad.dia_semana, Disponibilidad.hora_inicio)
        .all()
    )


def crear_disponibilidad(
    db: Session,
    *,
    medico_id: uuid.UUID,
    dia_semana: int,
    hora_inicio: time,
    hora_fin: time,
) -> Disponibilidad:
    """Define una franja para un médico. Valida el médico y el orden de las horas.

    Hace flush (no commit): el commit lo hace el endpoint.
    """
    medico = db.get(Usuario, medico_id)
    if medico is None or medico.rol != Rol.MEDICO:
        raise MedicoNoEncontrado()
    if hora_inicio >= hora_fin:
        raise FranjaInvalida()

    franja = Disponibilidad(
        usuario_id=medico_id,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
    )
    db.add(franja)
    db.flush()
    return franja
