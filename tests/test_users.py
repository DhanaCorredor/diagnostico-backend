"""Tests of the staff/doctor management (CRUD): create, list, view, edit and erase."""

import uuid
from datetime import datetime, time, timedelta

import pytest

from app.enums import AppointmentStatus, Role, ServiceCategory
from app.models import Appointment, Availability, Service, Specialty, User

from app.services import catalog as C
from app.services import users as U

NOW = datetime(2027, 1, 1, 8, 0)


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


def test_create_user_duplicate_email_ignoring_case(db):
    email = f"dup-{uuid.uuid4()}@test.local"
    _create(db, email=email)
    with pytest.raises(U.DuplicateEmail):
        _create(db, email=email.upper())


def test_create_user_specialty_not_found(db):
    with pytest.raises(C.SpecialtyNotFound):
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


def test_deactivate_user_via_put(db):
    u = _create(db, rol=Role.MEDICO)
    assert u.activo is True
    U.update_user(db, u.id, {"activo": False})
    assert u.activo is False


def test_reactivate_user_via_put(db):
    u = _create(db, rol=Role.MEDICO)
    U.update_user(db, u.id, {"activo": False})
    U.update_user(db, u.id, {"activo": True})
    assert u.activo is True


def _appointment_for(db, doctor, *, starts_at, creado_por=None):
    """Give the doctor one appointment, so erasing has to keep the record."""
    patient = User(nombre_completo=f"P {uuid.uuid4()}", edad=30, rol=Role.PACIENTE)
    service = Service(nombre=f"Serv {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA)
    db.add_all([patient, service])
    db.flush()
    db.add(
        Appointment(
            paciente_id=patient.id,
            medico_id=doctor.id,
            servicio_id=service.id,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(minutes=45),
            estado=AppointmentStatus.SCHEDULED,
            creado_por_id=(creado_por or doctor).id,
        )
    )
    db.flush()


def test_erase_user_without_history_deletes_the_row(db, admin):
    u = _create(db, rol=Role.MEDICO)
    resultado, citas = U.erase_user(db, u.id, requested_by_id=admin.id, now=NOW)
    assert (resultado, citas) == ("eliminado", 0)
    assert db.get(User, u.id) is None


def test_erase_user_with_past_appointments_wipes_the_personal_data(db, admin):
    u = _create(db, rol=Role.MEDICO)
    _appointment_for(db, u, starts_at=datetime(2026, 1, 5, 10, 0))

    resultado, citas = U.erase_user(db, u.id, requested_by_id=admin.id, now=NOW)

    assert (resultado, citas) == ("anonimizado", 1)
    assert u.nombre_completo == "Usuario eliminado"
    assert u.email is None
    assert u.password_hash is None
    assert u.matricula is None
    assert u.activo is False


def test_erase_user_blocked_when_it_has_upcoming_appointments(db, admin):
    u = _create(db, rol=Role.MEDICO)
    _appointment_for(db, u, starts_at=datetime(2027, 6, 7, 10, 0))
    with pytest.raises(U.UserHasUpcomingAppointments) as excinfo:
        U.erase_user(db, u.id, requested_by_id=admin.id, now=NOW)
    assert excinfo.value.count == 1


def test_erase_user_cannot_erase_itself(db):
    u = _create(db, rol=Role.ADMIN, matricula=None)
    with pytest.raises(U.CannotEraseSelf):
        U.erase_user(db, u.id, requested_by_id=u.id, now=NOW)


def test_erase_user_drops_schedule_and_specialties(db, admin):
    spec = Specialty(nombre=f"Esp {uuid.uuid4()}")
    db.add(spec)
    db.flush()
    u = _create(db, rol=Role.MEDICO, especialidades=[spec.id])
    db.add(
        Availability(
            usuario_id=u.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(12, 0)
        )
    )
    db.flush()
    _appointment_for(db, u, starts_at=datetime(2026, 1, 5, 10, 0))

    U.erase_user(db, u.id, requested_by_id=admin.id, now=NOW)

    assert u.especialidades == []
    assert db.query(Availability).filter(Availability.usuario_id == u.id).count() == 0
