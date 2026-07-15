"""Lógica de negocio de las citas: duración, disponibilidad y anti-solapamiento.

Estas funciones son el núcleo del proyecto. Viven separadas de los endpoints
para poder probarlas de forma aislada.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Cita, Disponibilidad, EstadoCita, Servicio


def calcular_ends_at(starts_at: datetime, servicio: Servicio) -> datetime:
    """Calcula cuándo termina la cita: inicio + la duración que marca el servicio.

    La cita no guarda su propia duración; la hereda del servicio en este momento.
    Ej.: 10:00 + Consulta (45 min) -> 10:45.
    """
    return starts_at + timedelta(minutes=servicio.duracion_min)


def dentro_de_disponibilidad(
    db: Session, medico_id: uuid.UUID, starts_at: datetime, ends_at: datetime
) -> bool:
    """Comprueba si la cita cae ENTERA dentro de alguna franja del médico ese día.

    - Convierte el día de la semana a la convención del modelo (0=domingo).
    - La cita es válida si su inicio y su fin caben dentro de una misma franja.
    (Asume que la cita no cruza la medianoche, cierto en un centro de salud.)
    """
    dia_semana = (starts_at.weekday() + 1) % 7  # Python: lunes=0 -> modelo: domingo=0
    hora_inicio = starts_at.time()
    hora_fin = ends_at.time()

    franjas = (
        db.query(Disponibilidad)
        .filter(Disponibilidad.usuario_id == medico_id)
        .filter(Disponibilidad.dia_semana == dia_semana)
        .all()
    )
    return any(
        f.hora_inicio <= hora_inicio and hora_fin <= f.hora_fin for f in franjas
    )


def hay_solapamiento(
    db: Session,
    medico_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    excluir_cita_id: uuid.UUID | None = None,
) -> bool:
    """Indica si el médico ya tiene una cita ACTIVA que se cruza con este horario.

    Dos citas se cruzan si:  nueva.inicio < existente.fin  Y  nueva.fin > existente.inicio.
    - Solo cuentan las activas (SCHEDULED / CONFIRMED); una CANCELLED libera el hueco.
    - Citas pegadas (una acaba justo cuando empieza la otra) NO se solapan.
    - excluir_cita_id: al editar una cita, se ignora ella misma.
    """
    q = (
        db.query(Cita)
        .filter(Cita.medico_id == medico_id)
        .filter(Cita.estado.in_([EstadoCita.SCHEDULED, EstadoCita.CONFIRMED]))
        .filter(Cita.starts_at < ends_at)  # la existente empieza antes de que acabe la nueva
        .filter(Cita.ends_at > starts_at)  # y termina después de que empiece la nueva
    )
    if excluir_cita_id is not None:
        q = q.filter(Cita.id != excluir_cita_id)
    return db.query(q.exists()).scalar()
