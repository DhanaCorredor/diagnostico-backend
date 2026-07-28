"""Tests de disponibilidad: listar franjas + crear con sus validaciones."""

import uuid
from datetime import time

import pytest

from app.enums import Role
from app.models import User
from app.services import availability as D


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
