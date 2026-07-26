"""Lógica de negocio de las citas: duración, disponibilidad y anti-solapamiento."""

import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.enums import AppointmentStatus, Role
from app.models import Appointment, Availability, Service, User
from app.services.patients import find_or_create_patient, get_patient

GRID_MINUTES = 15

CENTER_TZ = timezone(timedelta(hours=-4))


def now_center() -> datetime:
    """Hora actual en la zona del centro (UTC-4), naive (sin tzinfo)."""
    return datetime.now(CENTER_TZ).replace(tzinfo=None)


class ServiceNotFound(Exception):
    """El servicio indicado no existe."""


class DoctorNotFound(Exception):
    """El médico indicado no existe o no tiene rol MEDICO."""


class OutsideAvailability(Exception):
    """La cita cae fuera de la disponibilidad del médico (se puede forzar con sobrecupo)."""


class Overlap(Exception):
    """El médico ya tiene una cita activa que se cruza con este horario."""


class TimeNotAligned(Exception):
    """El inicio no cae en la rejilla de minutos permitida (:00, :15, :30, :45)."""


class AppointmentInThePast(Exception):
    """El inicio de la cita ya pasó; no se puede agendar en el pasado."""


class AppointmentNotFound(Exception):
    """No existe ninguna cita con ese id."""


class AppointmentNotCancellable(Exception):
    """La cita no se puede cancelar (ya está cancelada o completada)."""


class AppointmentNotActive(Exception):
    """La cita no está activa (SCHEDULED/CONFIRMED): no se puede marcar su asistencia."""


class AppointmentNotEditable(Exception):
    """La cita no está activa (ya cancelada o cerrada): no se puede editar ni mover."""


def is_aligned(starts_at: datetime) -> bool:
    """True si el inicio cae en la rejilla de GRID_MINUTOS, sin segundos ni microsegundos."""
    return (
        starts_at.minute % GRID_MINUTES == 0
        and starts_at.second == 0
        and starts_at.microsecond == 0
    )


def calculate_ends_at(starts_at: datetime, duracion_min: int) -> datetime:
    """Fin de la cita: inicio + la duración elegida (en minutos)."""
    return starts_at + timedelta(minutes=duracion_min)


def within_availability(
    db: Session, medico_id: uuid.UUID, starts_at: datetime, ends_at: datetime
) -> bool:
    """True si la cita cabe entera dentro de alguna franja del médico ese día."""
    dia_semana = (starts_at.weekday() + 1) % 7
    hora_inicio = starts_at.time()
    hora_fin = ends_at.time()

    slots = (
        db.query(Availability)
        .filter(Availability.usuario_id == medico_id)
        .filter(Availability.dia_semana == dia_semana)
        .all()
    )
    return any(
        f.hora_inicio <= hora_inicio and hora_fin <= f.hora_fin for f in slots
    )


def has_overlap(
    db: Session,
    medico_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    exclude_appointment_id: uuid.UUID | None = None,
) -> bool:
    """True si el médico ya tiene una cita activa cruzada con este horario.

    Solo cuentan las activas (una CANCELLED libera el hueco); las pegadas no se cruzan.
    `exclude_appointment_id` omite una cita (al mover, para que no choque consigo misma).
    """
    q = (
        db.query(Appointment)
        .filter(Appointment.medico_id == medico_id)
        .filter(Appointment.estado.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]))
        .filter(Appointment.starts_at < ends_at)
        .filter(Appointment.ends_at > starts_at)
    )
    if exclude_appointment_id is not None:
        q = q.filter(Appointment.id != exclude_appointment_id)
    return db.query(q.exists()).scalar()


def _validate_service_doctor_and_grid(
    db: Session,
    *,
    servicio_id: uuid.UUID,
    medico_id: uuid.UUID,
    starts_at: datetime,
) -> None:
    """Valida servicio activo, médico activo con rol MEDICO y rejilla de minutos (crear/editar)."""
    service = db.get(Service, servicio_id)
    if service is None or not service.activo:
        raise ServiceNotFound()
    doctor = db.get(User, medico_id)
    if doctor is None or doctor.rol != Role.MEDICO or not doctor.activo:
        raise DoctorNotFound()
    if not is_aligned(starts_at):
        raise TimeNotAligned()


def _validate_slot(
    db: Session,
    *,
    medico_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    permitir_sobrecupo: bool,
    exclude_appointment_id: uuid.UUID | None = None,
) -> None:
    """Valida disponibilidad (salvo sobrecupo) y anti-solapamiento del hueco (crear/editar)."""
    if not permitir_sobrecupo and not within_availability(
        db, medico_id, starts_at, ends_at
    ):
        raise OutsideAvailability()
    if has_overlap(db, medico_id, starts_at, ends_at, exclude_appointment_id=exclude_appointment_id):
        raise Overlap()


def create_appointment(
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
    now: datetime | None = None,
) -> Appointment:
    """Valida las reglas y crea la cita (upsert del paciente incluido). Flush, no commit.

    `now` se inyecta para poder probar en test la regla de "no en el pasado".
    """
    _validate_service_doctor_and_grid(
        db, servicio_id=servicio_id, medico_id=medico_id, starts_at=starts_at
    )

    if now is None:
        now = now_center()
    if starts_at < now:
        raise AppointmentInThePast()

    if paciente_id is not None:
        patient = get_patient(db, paciente_id)
    else:
        patient = find_or_create_patient(db, nombre_completo, edad)

    ends_at = calculate_ends_at(starts_at, duracion_min)

    _validate_slot(
        db,
        medico_id=medico_id,
        starts_at=starts_at,
        ends_at=ends_at,
        permitir_sobrecupo=permitir_sobrecupo,
    )

    appointment = Appointment(
        paciente_id=patient.id,
        medico_id=medico_id,
        servicio_id=servicio_id,
        starts_at=starts_at,
        ends_at=ends_at,
        estado=AppointmentStatus.SCHEDULED,
        motivo=motivo,
        creado_por_id=creado_por_id,
    )
    db.add(appointment)
    db.flush()
    return appointment


def list_appointments(
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
    start = datetime.combine(desde, time.min)
    end = datetime.combine(hasta, time.min) + timedelta(days=1)
    q = db.query(Appointment).filter(Appointment.starts_at >= start).filter(Appointment.starts_at < end)
    if medico_id is not None:
        q = q.filter(Appointment.medico_id == medico_id)
    if not incluir_canceladas:
        q = q.filter(Appointment.estado != AppointmentStatus.CANCELLED)
    return q.order_by(Appointment.starts_at).all()


def list_patient_appointments(db: Session, paciente_id: uuid.UUID) -> list[Appointment]:
    """Historial completo de un paciente (todas sus citas, de la más reciente a la más antigua)."""
    return (
        db.query(Appointment)
        .filter(Appointment.paciente_id == paciente_id)
        .order_by(Appointment.starts_at.desc())
        .all()
    )


def _get_active_appointment(
    db: Session, cita_id: uuid.UUID, exc_not_active: type[Exception]
) -> Appointment:
    """Devuelve la cita activa (SCHEDULED/CONFIRMED); lanza si no existe o ya está cerrada."""
    appointment = db.get(Appointment, cita_id)
    if appointment is None:
        raise AppointmentNotFound()
    if appointment.estado not in (AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED):
        raise exc_not_active()
    return appointment


def cancel_appointment(db: Session, cita_id: uuid.UUID) -> Appointment:
    """Cancela una cita activa (estado CANCELLED, libera el cupo). Flush, no commit."""
    appointment = _get_active_appointment(db, cita_id, AppointmentNotCancellable)
    appointment.estado = AppointmentStatus.CANCELLED
    db.flush()
    return appointment


def mark_attendance(db: Session, cita_id: uuid.UUID, estado: AppointmentStatus) -> Appointment:
    """Marca una cita activa como atendida (COMPLETED) o no-show (NO_SHOW). Flush, no commit."""
    appointment = _get_active_appointment(db, cita_id, AppointmentNotActive)
    appointment.estado = estado
    db.flush()
    return appointment


def edit_appointment(
    db: Session,
    cita_id: uuid.UUID,
    *,
    medico_id: uuid.UUID | None = None,
    servicio_id: uuid.UUID | None = None,
    starts_at: datetime | None = None,
    duracion_min: int | None = None,
    motivo: str | None = None,
    permitir_sobrecupo: bool = False,
    now: datetime | None = None,
) -> Appointment:
    """Edita o mueve una cita activa, revalidando las reglas de creación (excluye la propia cita).

    Actualización parcial: los campos en None se dejan igual. No cambia el paciente.
    La regla de "no en el pasado" solo aplica si se mueve la hora. Flush, no commit.
    """
    appointment = _get_active_appointment(db, cita_id, AppointmentNotEditable)

    new_doctor_id = medico_id if medico_id is not None else appointment.medico_id
    new_service_id = servicio_id if servicio_id is not None else appointment.servicio_id
    new_starts_at = starts_at if starts_at is not None else appointment.starts_at
    current_duration = int((appointment.ends_at - appointment.starts_at).total_seconds() // 60)
    new_duration = duracion_min if duracion_min is not None else current_duration

    _validate_service_doctor_and_grid(
        db, servicio_id=new_service_id, medico_id=new_doctor_id, starts_at=new_starts_at
    )

    if starts_at is not None:
        if now is None:
            now = now_center()
        if new_starts_at < now:
            raise AppointmentInThePast()

    new_ends_at = calculate_ends_at(new_starts_at, new_duration)

    same_slot = medico_id is None and starts_at is None and duracion_min is None
    _validate_slot(
        db,
        medico_id=new_doctor_id,
        starts_at=new_starts_at,
        ends_at=new_ends_at,
        permitir_sobrecupo=permitir_sobrecupo or same_slot,
        exclude_appointment_id=appointment.id,
    )

    appointment.medico_id = new_doctor_id
    appointment.servicio_id = new_service_id
    appointment.starts_at = new_starts_at
    appointment.ends_at = new_ends_at
    if motivo is not None:
        appointment.motivo = motivo
    db.flush()
    return appointment
