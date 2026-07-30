"""Availability tests: list, create, edit and remove slots, with their validations."""

import uuid
from datetime import datetime, time, timedelta

import pytest

from app.enums import AppointmentStatus, Role
from app.models import Appointment, User
from app.services import availability as D

NOW = datetime(2027, 1, 1, 8, 0)
FUTURE = datetime(2027, 6, 7, 10, 0)
FUTURE_DAY = (FUTURE.weekday() + 1) % 7


def _slot(db, doctor, hora_inicio=time(8, 0), hora_fin=time(14, 0)):
    return D.create_availability(
        db,
        medico_id=doctor.id,
        dia_semana=FUTURE_DAY,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
    )


def _booking(db, doctor, service, admin, starts_at=FUTURE, minutes=45,
             estado=AppointmentStatus.SCHEDULED):
    patient = User(nombre_completo=f"P {uuid.uuid4()}", edad=30, rol=Role.PACIENTE)
    db.add(patient)
    db.flush()
    ends_at = starts_at + timedelta(minutes=minutes)
    db.add(
        Appointment(
            paciente_id=patient.id,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=starts_at,
            ends_at=ends_at,
            estado=estado,
            creado_por_id=admin.id,
        )
    )
    db.flush()


def test_create_and_list_availability(db, doctor):
    D.create_availability(
        db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(14, 0)
    )
    slots = D.list_availability(db, doctor.id)
    assert len(slots) == 1
    assert slots[0].dia_semana == 1
    assert slots[0].hora_inicio == time(8, 0)


def test_create_availability_invalid_doctor(db, admin):
    with pytest.raises(D.DoctorNotFound):
        D.create_availability(
            db, medico_id=admin.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(14, 0)
        )


def test_create_availability_invalid_slot(db, doctor):
    with pytest.raises(D.InvalidSlot):
        D.create_availability(
            db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(14, 0), hora_fin=time(8, 0)
        )


def test_create_availability_overlapping_slot(db, doctor):
    D.create_availability(
        db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(12, 0)
    )
    with pytest.raises(D.OverlappingSlot):
        D.create_availability(
            db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(10, 0), hora_fin=time(14, 0)
        )


def test_create_availability_duplicate_slot(db, doctor):
    D.create_availability(
        db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(12, 0)
    )
    with pytest.raises(D.OverlappingSlot):
        D.create_availability(
            db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(12, 0)
        )


def test_create_availability_contained_slot(db, doctor):
    D.create_availability(
        db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(16, 0)
    )
    with pytest.raises(D.OverlappingSlot):
        D.create_availability(
            db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(10, 0), hora_fin=time(11, 0)
        )


def test_create_availability_contiguous_slots_allowed(db, doctor):
    D.create_availability(
        db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(12, 0)
    )
    D.create_availability(
        db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(12, 0), hora_fin=time(16, 0)
    )
    assert len(D.list_availability(db, doctor.id)) == 2


def test_create_availability_same_hours_other_day_allowed(db, doctor):
    D.create_availability(
        db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(12, 0)
    )
    D.create_availability(
        db, medico_id=doctor.id, dia_semana=2, hora_inicio=time(8, 0), hora_fin=time(12, 0)
    )
    assert len(D.list_availability(db, doctor.id)) == 2


def test_create_availability_same_hours_other_doctor_allowed(db, doctor):
    other = User(
        nombre_completo="Dra. Test Dos",
        rol=Role.MEDICO,
        email=f"med-{uuid.uuid4()}@test.local",
    )
    db.add(other)
    db.flush()

    D.create_availability(
        db, medico_id=doctor.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(12, 0)
    )
    D.create_availability(
        db, medico_id=other.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(12, 0)
    )
    assert len(D.list_availability(db, doctor.id)) == 1
    assert len(D.list_availability(db, other.id)) == 1


def test_update_availability_changes_hours(db, doctor):
    slot = _slot(db, doctor)
    updated = D.update_availability(
        db, franja_id=slot.id, hora_inicio=time(9, 0), hora_fin=time(15, 0), now=NOW
    )
    assert updated.hora_inicio == time(9, 0)
    assert updated.hora_fin == time(15, 0)


def test_update_availability_partial_keeps_the_rest(db, doctor):
    slot = _slot(db, doctor)
    updated = D.update_availability(db, franja_id=slot.id, hora_fin=time(16, 0), now=NOW)
    assert updated.hora_inicio == time(8, 0)
    assert updated.hora_fin == time(16, 0)
    assert updated.dia_semana == FUTURE_DAY


def test_update_availability_not_found(db):
    with pytest.raises(D.SlotNotFound):
        D.update_availability(db, franja_id=uuid.uuid4(), hora_fin=time(16, 0), now=NOW)


def test_update_availability_invalid_slot(db, doctor):
    slot = _slot(db, doctor)
    with pytest.raises(D.InvalidSlot):
        D.update_availability(db, franja_id=slot.id, hora_inicio=time(15, 0), now=NOW)


def test_update_availability_overlapping_another_slot(db, doctor):
    _slot(db, doctor, time(8, 0), time(12, 0))
    other = _slot(db, doctor, time(14, 0), time(18, 0))
    with pytest.raises(D.OverlappingSlot):
        D.update_availability(db, franja_id=other.id, hora_inicio=time(11, 0), now=NOW)


def test_update_availability_does_not_clash_with_itself(db, doctor):
    slot = _slot(db, doctor, time(8, 0), time(12, 0))
    updated = D.update_availability(db, franja_id=slot.id, hora_fin=time(13, 0), now=NOW)
    assert updated.hora_fin == time(13, 0)


def test_update_availability_blocked_when_it_strands_a_booking(db, doctor, service, admin):
    slot = _slot(db, doctor, time(8, 0), time(14, 0))
    _booking(db, doctor, service, admin)
    with pytest.raises(D.StrandedAppointments):
        D.update_availability(db, franja_id=slot.id, hora_fin=time(10, 0), now=NOW)


def test_update_availability_allowed_when_the_booking_still_fits(db, doctor, service, admin):
    slot = _slot(db, doctor, time(8, 0), time(14, 0))
    _booking(db, doctor, service, admin)
    updated = D.update_availability(db, franja_id=slot.id, hora_fin=time(18, 0), now=NOW)
    assert updated.hora_fin == time(18, 0)


def test_delete_availability(db, doctor):
    slot = _slot(db, doctor)
    D.delete_availability(db, slot.id, now=NOW)
    assert D.list_availability(db, doctor.id) == []


def test_delete_availability_not_found(db):
    with pytest.raises(D.SlotNotFound):
        D.delete_availability(db, uuid.uuid4(), now=NOW)


def test_delete_availability_blocked_when_it_has_bookings(db, doctor, service, admin):
    slot = _slot(db, doctor)
    _booking(db, doctor, service, admin)
    with pytest.raises(D.StrandedAppointments):
        D.delete_availability(db, slot.id, now=NOW)


def test_delete_availability_ignores_cancelled_bookings(db, doctor, service, admin):
    slot = _slot(db, doctor)
    _booking(db, doctor, service, admin, estado=AppointmentStatus.CANCELLED)
    D.delete_availability(db, slot.id, now=NOW)
    assert D.list_availability(db, doctor.id) == []


def test_delete_availability_ignores_past_bookings(db, doctor, service, admin):
    slot = _slot(db, doctor)
    _booking(db, doctor, service, admin)
    D.delete_availability(db, slot.id, now=datetime(2028, 1, 1, 8, 0))
    assert D.list_availability(db, doctor.id) == []
