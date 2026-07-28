"""Appointment business logic: duration, availability and overlap prevention."""

import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.enums import AppointmentStatus, Role
from app.models import Appointment, Availability, Service, User
from app.services.patients import find_or_create_patient, get_patient

GRID_MINUTES = 15

CENTER_TZ = timezone(timedelta(hours=-4))


def now_center() -> datetime:
    """Current time in the center's timezone (UTC-4), naive (without tzinfo)."""
    return datetime.now(CENTER_TZ).replace(tzinfo=None)


class ServiceNotFound(Exception):
    """The given service does not exist."""


class DoctorNotFound(Exception):
    """The given doctor does not exist or does not have the MEDICO role."""


class OutsideAvailability(Exception):
    """The appointment falls outside the doctor's availability (can be forced as an extra slot)."""


class Overlap(Exception):
    """The doctor already has an active appointment overlapping this time range."""


class TimeNotAligned(Exception):
    """The start time does not fall on the allowed minute grid (:00, :15, :30, :45)."""


class AppointmentInThePast(Exception):
    """The appointment start is already in the past; scheduling in the past is not allowed."""


class AppointmentNotFound(Exception):
    """There is no appointment with that id."""


class AppointmentNotCancellable(Exception):
    """The appointment cannot be cancelled (it is already cancelled or completed)."""


class AppointmentNotActive(Exception):
    """The appointment is not active (SCHEDULED/CONFIRMED): attendance cannot be marked."""


class AppointmentNotEditable(Exception):
    """The appointment is not active (already cancelled or closed): it cannot be edited or moved."""


def is_aligned(starts_at: datetime) -> bool:
    """True if the start falls on the GRID_MINUTES grid, with no seconds or microseconds."""
    return (
        starts_at.minute % GRID_MINUTES == 0
        and starts_at.second == 0
        and starts_at.microsecond == 0
    )


def calculate_ends_at(starts_at: datetime, duracion_min: int) -> datetime:
    """End of the appointment: start + the chosen duration (in minutes)."""
    return starts_at + timedelta(minutes=duracion_min)


def within_availability(
    db: Session, medico_id: uuid.UUID, starts_at: datetime, ends_at: datetime
) -> bool:
    """True if the appointment fits entirely inside one of the doctor's slots for that day."""
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
    """True if the doctor already has an active appointment overlapping this time range.

    Only active ones count (a CANCELLED one frees the slot); adjacent ones do not overlap.
    `exclude_appointment_id` skips one appointment (when moving, so it does not clash with itself).
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
    """Validate an active service, an active MEDICO-role doctor and the minute grid (create/edit)."""
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
    """Validate availability (unless it is an extra slot) and that the slot is free (create/edit)."""
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
    """Validate the rules and create the appointment (patient upsert included). Flush, no commit.

    `now` is injected so the "not in the past" rule can be tested.
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
    """Appointments in the range [desde, hasta] (both included), ordered by start time.

    `medico_id` filters by doctor; `incluir_canceladas` also includes the cancelled ones.
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
    """Full history of a patient (all their appointments, from the most recent to the oldest)."""
    return (
        db.query(Appointment)
        .filter(Appointment.paciente_id == paciente_id)
        .order_by(Appointment.starts_at.desc())
        .all()
    )


def _get_active_appointment(
    db: Session, cita_id: uuid.UUID, exc_not_active: type[Exception]
) -> Appointment:
    """Return the active appointment (SCHEDULED/CONFIRMED); raise if missing or already closed."""
    appointment = db.get(Appointment, cita_id)
    if appointment is None:
        raise AppointmentNotFound()
    if appointment.estado not in (AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED):
        raise exc_not_active()
    return appointment


def cancel_appointment(db: Session, cita_id: uuid.UUID) -> Appointment:
    """Cancel an active appointment (status CANCELLED, frees the slot). Flush, no commit."""
    appointment = _get_active_appointment(db, cita_id, AppointmentNotCancellable)
    appointment.estado = AppointmentStatus.CANCELLED
    db.flush()
    return appointment


def mark_attendance(db: Session, cita_id: uuid.UUID, estado: AppointmentStatus) -> Appointment:
    """Mark an active appointment as attended (COMPLETED) or missed (NO_SHOW). Flush, no commit."""
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
    """Edit or move an active appointment, revalidating the creation rules (excluding itself).

    Partial update: fields set to None are left unchanged. The patient is not changed.
    The "not in the past" rule only applies if the time is moved. Flush, no commit.
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
