"""Tests del upsert de paciente (R1)."""

import uuid

import pytest

from app.enums import Role
from app.models import User
from app.services.patients import (
    AmbiguousPatients,
    DuplicateNationalId,
    PatientNotFound,
    create_patient,
    deactivate_patient,
    find_or_create_patient,
    get_patient,
    list_patients,
    update_patient,
)


def test_creates_if_not_exists(db):
    nombre = f"Paciente {uuid.uuid4()}"
    p = find_or_create_patient(db, nombre, 40)
    assert p.id is not None
    assert p.rol == Role.PACIENTE
    assert p.nombre_completo == nombre


def test_reuses_if_exists(db):
    nombre = f"Paciente {uuid.uuid4()}"
    p1 = find_or_create_patient(db, nombre, 30)
    p2 = find_or_create_patient(db, nombre, 30)
    assert p1.id == p2.id


def test_multiple_matches_raises_ambiguous(db):
    nombre = f"Paciente {uuid.uuid4()}"
    db.add(User(nombre_completo=nombre, edad=50, rol=Role.PACIENTE))
    db.add(User(nombre_completo=nombre, edad=50, rol=Role.PACIENTE))
    db.flush()
    with pytest.raises(AmbiguousPatients) as exc:
        find_or_create_patient(db, nombre, 50)
    assert len(exc.value.candidatos) == 2


def test_list_patients_only_patients(db):
    pac = User(nombre_completo=f"Pac {uuid.uuid4()}", edad=40, rol=Role.PACIENTE)
    doctor = User(nombre_completo=f"Dr {uuid.uuid4()}", rol=Role.MEDICO)
    db.add_all([pac, doctor])
    db.flush()
    ids = [p.id for p in list_patients(db)]
    assert pac.id in ids
    assert doctor.id not in ids


def test_get_patient_ok_and_not_found(db):
    pac = User(nombre_completo=f"Pac {uuid.uuid4()}", edad=40, rol=Role.PACIENTE)
    db.add(pac)
    db.flush()
    assert get_patient(db, pac.id).id == pac.id
    with pytest.raises(PatientNotFound):
        get_patient(db, uuid.uuid4())


def test_update_patient(db):
    pac = find_or_create_patient(db, f"Pac {uuid.uuid4()}", 40)
    actualizado = update_patient(db, pac.id, {"nombre_completo": "Nuevo Nombre", "edad": 41})
    assert actualizado.nombre_completo == "Nuevo Nombre"
    assert actualizado.edad == 41


def test_update_patient_partial_keeps_national_id(db):
    pac = find_or_create_patient(db, f"Pac {uuid.uuid4()}", 40)
    pac.cedula = f"V-{uuid.uuid4()}"
    db.flush()
    ced_original = pac.cedula
    update_patient(db, pac.id, {"telefono": "555-9999"})
    assert pac.cedula == ced_original
    assert pac.telefono == "555-9999"


def test_create_patient_manual(db):
    datos = {
        "nombre_completo": f"Pac {uuid.uuid4()}",
        "edad": 33,
        "cedula": None,
        "telefono": None,
        "fecha_nacimiento": None,
    }
    p = create_patient(db, datos)
    assert p.id is not None
    assert p.rol == Role.PACIENTE
    assert p.edad == 33


def test_create_patient_duplicate_national_id(db):
    ced = f"CED-{uuid.uuid4()}"
    db.add(User(nombre_completo=f"Otro {uuid.uuid4()}", edad=30, rol=Role.PACIENTE, cedula=ced))
    db.flush()
    with pytest.raises(DuplicateNationalId):
        create_patient(
            db,
            {"nombre_completo": "X", "edad": 20, "cedula": ced, "telefono": None, "fecha_nacimiento": None},
        )


def test_update_patient_duplicate_national_id(db):
    ced = f"CED-{uuid.uuid4()}"
    otro = User(nombre_completo=f"Otro {uuid.uuid4()}", edad=30, rol=Role.PACIENTE, cedula=ced)
    db.add(otro)
    db.flush()
    pac = find_or_create_patient(db, f"Pac {uuid.uuid4()}", 40)
    with pytest.raises(DuplicateNationalId):
        update_patient(db, pac.id, {"cedula": ced})


def test_deactivate_patient_soft_delete(db):
    pac = find_or_create_patient(db, f"Pac {uuid.uuid4()}", 40)
    desactivado = deactivate_patient(db, pac.id)
    assert desactivado.activo is False
    assert pac.id not in [p.id for p in list_patients(db)]
