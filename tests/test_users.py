"""Tests of the staff/doctor management (CRUD): create, list, view, edit."""

import uuid

import pytest

from app.enums import Role
from app.models import Specialty, User
from app.services import users as U


def _create(db, **over):
    """Create a staff user with default data (a doctor), which can be overridden."""
    base = dict(
        nombre_completo=f"Dr {uuid.uuid4()}",
        rol=Role.MEDICO,
        email=f"u-{uuid.uuid4()}@test.local",
        password="password123",
        matricula=None,
        especialidades=[],
    )
    base.update(over)
    return U.create_user(db, **base)


def test_create_user_hashes_password(db):
    u = _create(db, rol=Role.RECEPCION)
    assert u.id is not None
    assert u.password_hash and u.password_hash != "password123"


def test_create_doctor_with_specialties(db):
    spec = Specialty(nombre=f"Cardio {uuid.uuid4()}")
    db.add(spec)
    db.flush()
    u = _create(db, rol=Role.MEDICO, especialidades=[spec.id])
    assert spec.id in [e.id for e in u.especialidades]


def test_create_user_patient_role_not_allowed(db):
    with pytest.raises(U.RoleNotAllowed):
        _create(db, rol=Role.PACIENTE)


def test_create_user_duplicate_email(db):
    email = f"dup-{uuid.uuid4()}@test.local"
    _create(db, email=email)
    with pytest.raises(U.DuplicateEmail):
        _create(db, email=email)


def test_create_user_specialty_not_found(db):
    with pytest.raises(U.SpecialtyNotFound):
        _create(db, especialidades=[uuid.uuid4()])


def test_non_doctor_with_specialties_fails(db):
    spec = Specialty(nombre=f"E {uuid.uuid4()}")
    db.add(spec)
    db.flush()
    with pytest.raises(U.DoctorOnlyData):
        _create(db, rol=Role.RECEPCION, especialidades=[spec.id])


def test_non_doctor_with_license_fails(db):
    with pytest.raises(U.DoctorOnlyData):
        _create(db, rol=Role.ADMIN, matricula="MAT-1")


def test_list_staff_excludes_patients(db):
    med = _create(db, rol=Role.MEDICO)
    pac = User(nombre_completo=f"Pac {uuid.uuid4()}", edad=30, rol=Role.PACIENTE)
    db.add(pac)
    db.flush()
    ids = [u.id for u in U.list_staff(db)]
    assert med.id in ids
    assert pac.id not in ids


def test_get_user_not_found(db):
    with pytest.raises(U.UserNotFound):
        U.get_user(db, uuid.uuid4())


def test_update_user_partial_keeps_password(db):
    u = _create(db, rol=Role.RECEPCION)
    hash_original = u.password_hash
    U.update_user(db, u.id, {"nombre_completo": "Nuevo"})
    assert u.nombre_completo == "Nuevo"
    assert u.password_hash == hash_original


def test_update_user_changes_password(db):
    u = _create(db, rol=Role.RECEPCION)
    hash_original = u.password_hash
    U.update_user(db, u.id, {"password": "nuevopass1"})
    assert u.password_hash != hash_original


def test_update_user_duplicate_email(db):
    otro = _create(db, rol=Role.RECEPCION)
    u = _create(db, rol=Role.MEDICO)
    with pytest.raises(U.DuplicateEmail):
        U.update_user(db, u.id, {"email": otro.email})


def test_update_user_specialties(db):
    spec = Specialty(nombre=f"Neuro {uuid.uuid4()}")
    db.add(spec)
    db.flush()
    u = _create(db, rol=Role.MEDICO)
    U.update_user(db, u.id, {"especialidades": [spec.id]})
    assert spec.id in [e.id for e in u.especialidades]


def test_update_user_not_found(db):
    with pytest.raises(U.UserNotFound):
        U.update_user(db, uuid.uuid4(), {"nombre_completo": "X"})


def test_deactivate_user(db):
    u = _create(db, rol=Role.MEDICO)
    assert u.activo is True
    U.deactivate_user(db, u.id)
    assert u.activo is False


def test_reactivate_user_via_put(db):
    u = _create(db, rol=Role.MEDICO)
    U.deactivate_user(db, u.id)
    U.update_user(db, u.id, {"activo": True})
    assert u.activo is True
