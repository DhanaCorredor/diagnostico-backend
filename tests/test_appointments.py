"""Tests de las reglas de citas (R2, R3, R4) y del orquestador crear_cita."""

import uuid
from datetime import date, datetime, time, timezone

import pytest
from pydantic import ValidationError

from app.enums import AppointmentStatus, Role
from app.models import Appointment, Availability, User
from app.schemas import AppointmentCreate, AppointmentUpdate
from app.services import appointments as C

LUNES_10 = datetime(2026, 7, 20, 10, 0)
DIA_LUNES = (LUNES_10.weekday() + 1) % 7
ANTES = datetime(2026, 7, 20, 0, 0)


def _slot(db, doctor, hora_inicio=time(8, 0), hora_fin=time(14, 0)):
    db.add(
        Availability(
            usuario_id=doctor.id,
            dia_semana=DIA_LUNES,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        )
    )
    db.flush()


def test_appointmentcreate_rejects_tzaware_date():
    with pytest.raises(ValidationError):
        AppointmentCreate(
            nombre_completo="Ana",
            edad=30,
            medico_id=uuid.uuid4(),
            servicio_id=uuid.uuid4(),
            starts_at="2026-07-20T10:00:00Z",
            duracion_min=45,
        )


def test_appointmentcreate_accepts_naive_date():
    datos = AppointmentCreate(
        nombre_completo="Ana",
        edad=30,
        medico_id=uuid.uuid4(),
        servicio_id=uuid.uuid4(),
        starts_at="2026-07-20T10:00:00",
        duracion_min=45,
    )
    assert datos.starts_at == datetime(2026, 7, 20, 10, 0)


def test_appointmentupdate_rejects_tzaware_date():
    with pytest.raises(ValidationError):
        AppointmentUpdate(starts_at="2026-07-20T11:30:00+00:00")


def test_appointmentupdate_without_starts_at_ok():
    datos = AppointmentUpdate(motivo="control")
    assert datos.starts_at is None


def test_now_center_is_naive_and_utc_minus_4():
    got = C.now_center()
    assert got.tzinfo is None
    utc = datetime.now(timezone.utc).replace(tzinfo=None)
    horas_detras = (utc - got).total_seconds() / 3600
    assert 3.5 < horas_detras < 4.5


def test_calculate_ends_at():
    fin = C.calculate_ends_at(datetime(2026, 7, 20, 10, 0), 45)
    assert fin == datetime(2026, 7, 20, 10, 45)


def test_is_aligned():
    assert C.is_aligned(datetime(2026, 7, 20, 10, 0)) is True
    assert C.is_aligned(datetime(2026, 7, 20, 10, 30)) is True
    assert C.is_aligned(datetime(2026, 7, 20, 11, 45)) is True
    assert C.is_aligned(datetime(2026, 7, 20, 10, 7)) is False
    assert C.is_aligned(datetime(2026, 7, 20, 10, 15, 30)) is False


def test_create_appointment_unaligned_time(db, doctor, service, admin):
    _slot(db, doctor)
    with pytest.raises(C.TimeNotAligned):
        C.create_appointment(
            db,
            nombre_completo=f"X {uuid.uuid4()}",
            edad=1,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=datetime(2026, 7, 20, 10, 7),
            duracion_min=45,
            creado_por_id=admin.id,
        )


def test_availability_inside_and_outside(db, doctor):
    _slot(db, doctor)
    dentro = C.within_availability(
        db, doctor.id, datetime(2026, 7, 20, 10, 0), datetime(2026, 7, 20, 10, 45)
    )
    fuera = C.within_availability(
        db, doctor.id, datetime(2026, 7, 20, 7, 0), datetime(2026, 7, 20, 7, 45)
    )
    assert dentro is True
    assert fuera is False


def test_overlap_and_adjacent_appointments(db, doctor, service, admin):
    pac = User(nombre_completo=f"P {uuid.uuid4()}", edad=1, rol=Role.PACIENTE)
    db.add(pac)
    db.flush()
    db.add(
        Appointment(
            paciente_id=pac.id,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=datetime(2026, 7, 20, 10, 0),
            ends_at=datetime(2026, 7, 20, 10, 45),
            estado=AppointmentStatus.SCHEDULED,
            creado_por_id=admin.id,
        )
    )
    db.flush()
    assert C.has_overlap(
        db, doctor.id, datetime(2026, 7, 20, 10, 30), datetime(2026, 7, 20, 11, 0)
    ) is True
    assert C.has_overlap(
        db, doctor.id, datetime(2026, 7, 20, 10, 45), datetime(2026, 7, 20, 11, 30)
    ) is False


def test_create_appointment_happy_path(db, doctor, service, admin):
    _slot(db, doctor)
    appointment = C.create_appointment(
        db,
        nombre_completo=f"Ana {uuid.uuid4()}",
        edad=33,
        medico_id=doctor.id,
        servicio_id=service.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    assert appointment.ends_at == datetime(2026, 7, 20, 10, 45)
    assert appointment.estado == AppointmentStatus.SCHEDULED


def test_create_appointment_with_patient_id_resolves_ambiguity(db, doctor, service, admin):
    _slot(db, doctor)
    p1 = User(nombre_completo="Ambiguo", edad=40, rol=Role.PACIENTE)
    p2 = User(nombre_completo="Ambiguo", edad=40, rol=Role.PACIENTE)
    db.add_all([p1, p2])
    db.flush()
    appointment = C.create_appointment(
        db,
        nombre_completo="Ambiguo",
        edad=40,
        paciente_id=p1.id,
        medico_id=doctor.id,
        servicio_id=service.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    assert appointment.paciente_id == p1.id


def test_create_appointment_uses_chosen_duration(db, doctor, service, admin):
    _slot(db, doctor)
    appointment = C.create_appointment(
        db,
        nombre_completo=f"Dur {uuid.uuid4()}",
        edad=1,
        medico_id=doctor.id,
        servicio_id=service.id,
        starts_at=LUNES_10,
        duracion_min=90,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    assert appointment.ends_at == datetime(2026, 7, 20, 11, 30)


def test_create_appointment_outside_availability(db, doctor, service, admin):
    with pytest.raises(C.OutsideAvailability):
        C.create_appointment(
            db,
            nombre_completo=f"X {uuid.uuid4()}",
            edad=1,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
            ahora=ANTES,
        )


def test_create_appointment_blocks_overlap(db, doctor, service, admin):
    _slot(db, doctor)
    C.create_appointment(
        db,
        nombre_completo=f"A {uuid.uuid4()}",
        edad=1,
        medico_id=doctor.id,
        servicio_id=service.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    with pytest.raises(C.Overlap):
        C.create_appointment(
            db,
            nombre_completo=f"B {uuid.uuid4()}",
            edad=2,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=datetime(2026, 7, 20, 10, 30),
            duracion_min=45,
            creado_por_id=admin.id,
            ahora=ANTES,
        )


def test_create_appointment_invalid_doctor(db, service, admin):
    with pytest.raises(C.DoctorNotFound):
        C.create_appointment(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=admin.id,
            servicio_id=service.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
        )


def test_create_appointment_invalid_service(db, doctor, admin):
    with pytest.raises(C.ServiceNotFound):
        C.create_appointment(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=doctor.id,
            servicio_id=uuid.uuid4(),
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
        )


def test_create_appointment_inactive_service(db, doctor, service, admin):
    service.activo = False
    db.flush()
    with pytest.raises(C.ServiceNotFound):
        C.create_appointment(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
        )


def test_edit_appointment_overbook_only_reason(db, doctor, service, admin):
    appointment = C.create_appointment(
        db,
        nombre_completo=f"X {uuid.uuid4()}",
        edad=1,
        medico_id=doctor.id,
        servicio_id=service.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        permitir_sobrecupo=True,
        ahora=ANTES,
    )
    actualizada = C.edit_appointment(db, appointment.id, motivo="control")
    assert actualizada.motivo == "control"


def test_create_appointment_in_the_past(db, doctor, service, admin):
    _slot(db, doctor)
    with pytest.raises(C.AppointmentInThePast):
        C.create_appointment(
            db,
            nombre_completo=f"X {uuid.uuid4()}",
            edad=1,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
            ahora=datetime(2026, 7, 20, 11, 0),
        )


def test_create_appointment_inactive_doctor(db, service, admin):
    inactivo = User(
        nombre_completo=f"Dr. Baja {uuid.uuid4()}",
        rol=Role.MEDICO,
        email=f"baja-{uuid.uuid4()}@test.local",
        activo=False,
    )
    db.add(inactivo)
    db.flush()
    with pytest.raises(C.DoctorNotFound):
        C.create_appointment(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=inactivo.id,
            servicio_id=service.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
            ahora=ANTES,
        )


def _appointment(db, doctor, service, admin, starts_at):
    """Crea y devuelve una cita ya agendada (con franja disponible)."""
    _slot(db, doctor)
    return C.create_appointment(
        db,
        nombre_completo=f"P {uuid.uuid4()}",
        edad=1,
        medico_id=doctor.id,
        servicio_id=service.id,
        starts_at=starts_at,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )


FECHA_LUNES = LUNES_10.date()


def test_list_filters_by_doctor(db, doctor, service, admin):
    _appointment(db, doctor, service, admin, LUNES_10)
    del_medico = C.list_appointments(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=doctor.id)
    de_otro = C.list_appointments(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=uuid.uuid4())
    assert len(del_medico) == 1
    assert de_otro == []


def test_list_by_range_and_ordered(db, doctor, service, admin):
    _appointment(db, doctor, service, admin, datetime(2026, 7, 20, 11, 0))
    _appointment(db, doctor, service, admin, datetime(2026, 7, 20, 9, 0))
    del_dia = C.list_appointments(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=doctor.id)
    otro_dia = C.list_appointments(
        db, desde=date(2026, 7, 21), hasta=date(2026, 7, 21), medico_id=doctor.id
    )
    assert [c.starts_at.hour for c in del_dia] == [9, 11]
    assert otro_dia == []


def test_list_excludes_cancelled_by_default(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.cancel_appointment(db, appointment.id)
    vigentes = C.list_appointments(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=doctor.id)
    con_canceladas = C.list_appointments(
        db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=doctor.id, incluir_canceladas=True
    )
    assert vigentes == []
    assert len(con_canceladas) == 1


def test_cancel_appointment_frees_slot(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.cancel_appointment(db, appointment.id)
    assert appointment.estado == AppointmentStatus.CANCELLED
    otra = C.create_appointment(
        db,
        nombre_completo=f"Q {uuid.uuid4()}",
        edad=2,
        medico_id=doctor.id,
        servicio_id=service.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    assert otra.estado == AppointmentStatus.SCHEDULED


def test_cancel_appointment_not_found(db):
    with pytest.raises(C.AppointmentNotFound):
        C.cancel_appointment(db, uuid.uuid4())


def test_cancel_appointment_already_cancelled(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.cancel_appointment(db, appointment.id)
    with pytest.raises(C.AppointmentNotCancellable):
        C.cancel_appointment(db, appointment.id)


def test_mark_attendance_completed(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.mark_attendance(db, appointment.id, AppointmentStatus.COMPLETED)
    assert appointment.estado == AppointmentStatus.COMPLETED


def test_mark_attendance_no_show(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.mark_attendance(db, appointment.id, AppointmentStatus.NO_SHOW)
    assert appointment.estado == AppointmentStatus.NO_SHOW


def test_mark_attendance_not_found(db):
    with pytest.raises(C.AppointmentNotFound):
        C.mark_attendance(db, uuid.uuid4(), AppointmentStatus.COMPLETED)


def test_mark_attendance_appointment_not_active(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.cancel_appointment(db, appointment.id)
    with pytest.raises(C.AppointmentNotActive):
        C.mark_attendance(db, appointment.id, AppointmentStatus.COMPLETED)


def test_edit_moves_time(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.edit_appointment(db, appointment.id, starts_at=datetime(2026, 7, 20, 11, 0), ahora=ANTES)
    assert appointment.starts_at == datetime(2026, 7, 20, 11, 0)
    assert appointment.ends_at == datetime(2026, 7, 20, 11, 45)


def test_edit_changes_duration(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.edit_appointment(db, appointment.id, duracion_min=90, ahora=ANTES)
    assert appointment.ends_at == datetime(2026, 7, 20, 11, 30)


def test_edit_does_not_overlap_itself(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.edit_appointment(db, appointment.id, starts_at=datetime(2026, 7, 20, 10, 15), ahora=ANTES)
    assert appointment.starts_at == datetime(2026, 7, 20, 10, 15)


def test_edit_blocks_overlap_with_another(db, doctor, service, admin):
    _slot(db, doctor)
    otra = C.create_appointment(
        db,
        nombre_completo=f"Otra {uuid.uuid4()}",
        edad=1,
        medico_id=doctor.id,
        servicio_id=service.id,
        starts_at=datetime(2026, 7, 20, 9, 0),
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    with pytest.raises(C.Overlap):
        C.edit_appointment(db, appointment.id, starts_at=datetime(2026, 7, 20, 9, 30), ahora=ANTES)
    assert otra.id != appointment.id


def test_edit_appointment_not_found(db):
    with pytest.raises(C.AppointmentNotFound):
        C.edit_appointment(db, uuid.uuid4(), motivo="x")


def test_edit_appointment_not_active(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.cancel_appointment(db, appointment.id)
    with pytest.raises(C.AppointmentNotEditable):
        C.edit_appointment(db, appointment.id, motivo="x")


def test_edit_outside_availability(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    with pytest.raises(C.OutsideAvailability):
        C.edit_appointment(db, appointment.id, starts_at=datetime(2026, 7, 20, 7, 0), ahora=ANTES)


def test_edit_unaligned_time(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    with pytest.raises(C.TimeNotAligned):
        C.edit_appointment(db, appointment.id, starts_at=datetime(2026, 7, 20, 11, 7), ahora=ANTES)


def test_edit_to_the_past(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    with pytest.raises(C.AppointmentInThePast):
        C.edit_appointment(
            db,
            appointment.id,
            starts_at=datetime(2026, 7, 20, 11, 0),
            ahora=datetime(2026, 7, 20, 12, 0),
        )


def test_edit_without_moving_time_skips_past_check(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    C.edit_appointment(db, appointment.id, motivo="control", ahora=datetime(2026, 7, 20, 23, 0))
    assert appointment.motivo == "control"


def test_edit_reason_none_keeps_current(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    appointment.motivo = "revisión"
    db.flush()
    C.edit_appointment(db, appointment.id, starts_at=datetime(2026, 7, 20, 11, 0), ahora=ANTES)
    assert appointment.motivo == "revisión"


def test_list_patient_appointments_history(db, doctor, service, admin):
    appointment = _appointment(db, doctor, service, admin, LUNES_10)
    historial = C.list_patient_appointments(db, appointment.paciente_id)
    assert [c.id for c in historial] == [appointment.id]
