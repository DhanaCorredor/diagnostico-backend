"""Lógica de negocio de las citas: duración, disponibilidad y anti-solapamiento."""

import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.enums import AppointmentStatus, Role
from app.models import Appointment, Availability, Service, User
from app.services.pacientes import buscar_o_crear_paciente, obtener_paciente

GRID_MINUTOS = 15

ZONA_CENTRO = timezone(timedelta(hours=-4))


def ahora_centro() -> datetime:
    """Hora actual en la zona del centro (UTC-4), naive (sin tzinfo)."""
    return datetime.now(ZONA_CENTRO).replace(tzinfo=None)


class ServicioNoEncontrado(Exception):
    """El servicio indicado no existe."""


class MedicoNoEncontrado(Exception):
    """El médico indicado no existe o no tiene rol MEDICO."""


class FueraDeDisponibilidad(Exception):
    """La cita cae fuera de la disponibilidad del médico (se puede forzar con sobrecupo)."""


class Solapamiento(Exception):
    """El médico ya tiene una cita activa que se cruza con este horario."""


class HorarioNoAlineado(Exception):
    """El inicio no cae en la rejilla de minutos permitida (:00, :15, :30, :45)."""


class CitaEnElPasado(Exception):
    """El inicio de la cita ya pasó; no se puede agendar en el pasado."""


class CitaNoEncontrada(Exception):
    """No existe ninguna cita con ese id."""


class CitaNoCancelable(Exception):
    """La cita no se puede cancelar (ya está cancelada o completada)."""


class CitaNoActiva(Exception):
    """La cita no está activa (SCHEDULED/CONFIRMED): no se puede marcar su asistencia."""


class CitaNoEditable(Exception):
    """La cita no está activa (ya cancelada o cerrada): no se puede editar ni mover."""


def esta_alineado(starts_at: datetime) -> bool:
    """True si el inicio cae en la rejilla de GRID_MINUTOS, sin segundos ni microsegundos."""
    return (
        starts_at.minute % GRID_MINUTOS == 0
        and starts_at.second == 0
        and starts_at.microsecond == 0
    )


def calcular_ends_at(starts_at: datetime, duracion_min: int) -> datetime:
    """Fin de la cita: inicio + la duración elegida (en minutos)."""
    return starts_at + timedelta(minutes=duracion_min)


def dentro_de_disponibilidad(
    db: Session, medico_id: uuid.UUID, starts_at: datetime, ends_at: datetime
) -> bool:
    """True si la cita cabe entera dentro de alguna franja del médico ese día."""
    dia_semana = (starts_at.weekday() + 1) % 7
    hora_inicio = starts_at.time()
    hora_fin = ends_at.time()

    franjas = (
        db.query(Availability)
        .filter(Availability.usuario_id == medico_id)
        .filter(Availability.dia_semana == dia_semana)
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
    """True si el médico ya tiene una cita activa cruzada con este horario.

    Solo cuentan las activas (una CANCELLED libera el hueco); las pegadas no se cruzan.
    `excluir_cita_id` omite una cita (al mover, para que no choque consigo misma).
    """
    q = (
        db.query(Appointment)
        .filter(Appointment.medico_id == medico_id)
        .filter(Appointment.estado.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]))
        .filter(Appointment.starts_at < ends_at)
        .filter(Appointment.ends_at > starts_at)
    )
    if excluir_cita_id is not None:
        q = q.filter(Appointment.id != excluir_cita_id)
    return db.query(q.exists()).scalar()


def _validar_servicio_medico_y_rejilla(
    db: Session,
    *,
    servicio_id: uuid.UUID,
    medico_id: uuid.UUID,
    starts_at: datetime,
) -> None:
    """Valida servicio activo, médico activo con rol MEDICO y rejilla de minutos (crear/editar)."""
    servicio = db.get(Service, servicio_id)
    if servicio is None or not servicio.activo:
        raise ServicioNoEncontrado()
    medico = db.get(User, medico_id)
    if medico is None or medico.rol != Role.MEDICO or not medico.activo:
        raise MedicoNoEncontrado()
    if not esta_alineado(starts_at):
        raise HorarioNoAlineado()


def _validar_hueco(
    db: Session,
    *,
    medico_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    permitir_sobrecupo: bool,
    excluir_cita_id: uuid.UUID | None = None,
) -> None:
    """Valida disponibilidad (salvo sobrecupo) y anti-solapamiento del hueco (crear/editar)."""
    if not permitir_sobrecupo and not dentro_de_disponibilidad(
        db, medico_id, starts_at, ends_at
    ):
        raise FueraDeDisponibilidad()
    if hay_solapamiento(db, medico_id, starts_at, ends_at, excluir_cita_id=excluir_cita_id):
        raise Solapamiento()


def crear_cita(
    db: Session,
    *,
    nombre_completo: str,
    edad: int,
    paciente_id: uuid.UUID | None = None,
    medico_id: uuid.UUID,
    servicio_id: uuid.UUID,
    starts_at: datetime,
    duracion_min: int,
    creado_por_id: uuid.UUID,
    motivo: str | None = None,
    permitir_sobrecupo: bool = False,
    ahora: datetime | None = None,
) -> Appointment:
    """Valida las reglas y crea la cita (upsert del paciente incluido). Flush, no commit.

    `ahora` se inyecta para poder probar en test la regla de "no en el pasado".
    """
    _validar_servicio_medico_y_rejilla(
        db, servicio_id=servicio_id, medico_id=medico_id, starts_at=starts_at
    )

    if ahora is None:
        ahora = ahora_centro()
    if starts_at < ahora:
        raise CitaEnElPasado()

    if paciente_id is not None:
        paciente = obtener_paciente(db, paciente_id)
    else:
        paciente = buscar_o_crear_paciente(db, nombre_completo, edad)

    ends_at = calcular_ends_at(starts_at, duracion_min)

    _validar_hueco(
        db,
        medico_id=medico_id,
        starts_at=starts_at,
        ends_at=ends_at,
        permitir_sobrecupo=permitir_sobrecupo,
    )

    cita = Appointment(
        paciente_id=paciente.id,
        medico_id=medico_id,
        servicio_id=servicio_id,
        starts_at=starts_at,
        ends_at=ends_at,
        estado=AppointmentStatus.SCHEDULED,
        motivo=motivo,
        creado_por_id=creado_por_id,
    )
    db.add(cita)
    db.flush()
    return cita


def listar_citas(
    db: Session,
    *,
    desde: date,
    hasta: date,
    medico_id: uuid.UUID | None = None,
    incluir_canceladas: bool = False,
) -> list[Appointment]:
    """Citas del rango [desde, hasta] (ambos incluidos), ordenadas por inicio.

    `medico_id` filtra por médico; `incluir_canceladas` añade también las canceladas.
    """
    inicio = datetime.combine(desde, time.min)
    fin = datetime.combine(hasta, time.min) + timedelta(days=1)
    q = db.query(Appointment).filter(Appointment.starts_at >= inicio).filter(Appointment.starts_at < fin)
    if medico_id is not None:
        q = q.filter(Appointment.medico_id == medico_id)
    if not incluir_canceladas:
        q = q.filter(Appointment.estado != AppointmentStatus.CANCELLED)
    return q.order_by(Appointment.starts_at).all()


def listar_citas_de_paciente(db: Session, paciente_id: uuid.UUID) -> list[Appointment]:
    """Historial completo de un paciente (todas sus citas, de la más reciente a la más antigua)."""
    return (
        db.query(Appointment)
        .filter(Appointment.paciente_id == paciente_id)
        .order_by(Appointment.starts_at.desc())
        .all()
    )


def _obtener_cita_activa(
    db: Session, cita_id: uuid.UUID, exc_no_activa: type[Exception]
) -> Appointment:
    """Devuelve la cita activa (SCHEDULED/CONFIRMED); lanza si no existe o ya está cerrada."""
    cita = db.get(Appointment, cita_id)
    if cita is None:
        raise CitaNoEncontrada()
    if cita.estado not in (AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED):
        raise exc_no_activa()
    return cita


def cancelar_cita(db: Session, cita_id: uuid.UUID) -> Appointment:
    """Cancela una cita activa (estado CANCELLED, libera el cupo). Flush, no commit."""
    cita = _obtener_cita_activa(db, cita_id, CitaNoCancelable)
    cita.estado = AppointmentStatus.CANCELLED
    db.flush()
    return cita


def marcar_asistencia(db: Session, cita_id: uuid.UUID, estado: AppointmentStatus) -> Appointment:
    """Marca una cita activa como atendida (COMPLETED) o no-show (NO_SHOW). Flush, no commit."""
    cita = _obtener_cita_activa(db, cita_id, CitaNoActiva)
    cita.estado = estado
    db.flush()
    return cita


def editar_cita(
    db: Session,
    cita_id: uuid.UUID,
    *,
    medico_id: uuid.UUID | None = None,
    servicio_id: uuid.UUID | None = None,
    starts_at: datetime | None = None,
    duracion_min: int | None = None,
    motivo: str | None = None,
    permitir_sobrecupo: bool = False,
    ahora: datetime | None = None,
) -> Appointment:
    """Edita o mueve una cita activa, revalidando las reglas de creación (excluye la propia cita).

    Actualización parcial: los campos en None se dejan igual. No cambia el paciente.
    La regla de "no en el pasado" solo aplica si se mueve la hora. Flush, no commit.
    """
    cita = _obtener_cita_activa(db, cita_id, CitaNoEditable)

    nuevo_medico_id = medico_id if medico_id is not None else cita.medico_id
    nuevo_servicio_id = servicio_id if servicio_id is not None else cita.servicio_id
    nuevo_starts_at = starts_at if starts_at is not None else cita.starts_at
    duracion_actual = int((cita.ends_at - cita.starts_at).total_seconds() // 60)
    nueva_duracion = duracion_min if duracion_min is not None else duracion_actual

    _validar_servicio_medico_y_rejilla(
        db, servicio_id=nuevo_servicio_id, medico_id=nuevo_medico_id, starts_at=nuevo_starts_at
    )

    if starts_at is not None:
        if ahora is None:
            ahora = ahora_centro()
        if nuevo_starts_at < ahora:
            raise CitaEnElPasado()

    nuevo_ends_at = calcular_ends_at(nuevo_starts_at, nueva_duracion)

    mismo_hueco = medico_id is None and starts_at is None and duracion_min is None
    _validar_hueco(
        db,
        medico_id=nuevo_medico_id,
        starts_at=nuevo_starts_at,
        ends_at=nuevo_ends_at,
        permitir_sobrecupo=permitir_sobrecupo or mismo_hueco,
        excluir_cita_id=cita.id,
    )

    cita.medico_id = nuevo_medico_id
    cita.servicio_id = nuevo_servicio_id
    cita.starts_at = nuevo_starts_at
    cita.ends_at = nuevo_ends_at
    if motivo is not None:
        cita.motivo = motivo
    db.flush()
    return cita
