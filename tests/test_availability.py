"""Tests de disponibilidad: listar franjas + crear con sus validaciones."""

from datetime import time

import pytest

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
