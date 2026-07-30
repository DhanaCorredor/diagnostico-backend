"""Tests of the patient upsert (R1) and of erasing a patient for good."""

import uuid
from datetime import datetime

import pytest

from app.enums import AppointmentStatus, Role, ServiceCategory
from app.models import Appointment, Service, User
from app.services.patients import (
    AmbiguousPatients,
    DuplicateNationalId,
    PatientNotFound,
    create_patient,
    erase_patient,
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
    assert len(exc.value.candidates) == 2


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
    data = {
        "nombre_completo": f"Pac {uuid.uuid4()}",
        "edad": 33,
        "cedula": None,
        "telefono": None,
        "fecha_nacimiento": None,
    }
    p = create_patient(db, data)
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


def test_create_patient_duplicate_national_id_ignoring_case(db):
    ced = f"ced-{uuid.uuid4()}"
    db.add(User(nombre_completo=f"Otro {uuid.uuid4()}", edad=30, rol=Role.PACIENTE, cedula=ced))
    db.flush()
    with pytest.raises(DuplicateNationalId):
        create_patient(
            db,
            {
                "nombre_completo": "X",
                "edad": 20,
                "cedula": ced.upper(),
                "telefono": None,
                "fecha_nacimiento": None,
            },
        )


def test_update_patient_duplicate_national_id(db):
    ced = f"CED-{uuid.uuid4()}"
    otro = User(nombre_completo=f"Otro {uuid.uuid4()}", edad=30, rol=Role.PACIENTE, cedula=ced)
    db.add(otro)
    db.flush()
    pac = find_or_create_patient(db, f"Pac {uuid.uuid4()}", 40)
    with pytest.raises(DuplicateNationalId):
        update_patient(db, pac.id, {"cedula": ced})


def test_erase_patient_without_appointments_deletes_the_row(db):
    pac = find_or_create_patient(db, f"Pac {uuid.uuid4()}", 40)
    resultado, citas = erase_patient(db, pac.id)
    assert (resultado, citas) == ("eliminado", 0)
    assert db.get(User, pac.id) is None


def _with_appointment(db, patient):
    """Give the patient one appointment, so erasing has to keep the record."""
    doctor = User(
        nombre_completo="Dr. Borrado",
        rol=Role.MEDICO,
        email=f"med-{uuid.uuid4()}@test.local",
    )
    admin = User(
        nombre_completo="Admin Borrado",
        rol=Role.ADMIN,
        email=f"adm-{uuid.uuid4()}@test.local",
    )
    service = Service(nombre=f"Serv {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA)
    db.add_all([doctor, admin, service])
    db.flush()
    db.add(
        Appointment(
            paciente_id=patient.id,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=datetime(2027, 3, 1, 10, 0),
            ends_at=datetime(2027, 3, 1, 10, 45),
            estado=AppointmentStatus.SCHEDULED,
            creado_por_id=admin.id,
        )
    )
    db.flush()


def test_erase_patient_with_appointments_wipes_the_personal_data(db):
    pac = find_or_create_patient(db, f"Pac {uuid.uuid4()}", 40)
    pac.cedula = f"V-{uuid.uuid4().hex[:8]}"
    pac.telefono = "0412-0000000"
    db.flush()
    _with_appointment(db, pac)

    resultado, citas = erase_patient(db, pac.id)

    assert (resultado, citas) == ("anonimizado", 1)
    assert pac.nombre_completo == "Paciente eliminado"
    assert pac.cedula is None
    assert pac.telefono is None
    assert pac.edad is None
    assert pac.activo is False


def test_erased_patient_leaves_the_list_and_keeps_its_appointments(db):
    pac = find_or_create_patient(db, f"Pac {uuid.uuid4()}", 40)
    _with_appointment(db, pac)
    erase_patient(db, pac.id)

    assert pac.id not in [p.id for p in list_patients(db)]
    assert db.query(Appointment).filter(Appointment.paciente_id == pac.id).count() == 1


def test_erase_patient_not_found(db):
    with pytest.raises(PatientNotFound):
        erase_patient(db, uuid.uuid4())
