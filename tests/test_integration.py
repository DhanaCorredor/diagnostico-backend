"""HTTP integration tests (TestClient): auth, role guards and the appointment flow.

They cover the layer the service tests do NOT touch: authentication, role
dependencies, serialization and the real API contract end to end. Ported from
the manual smoke test so they are repeatable and run in CI.
"""

import uuid
from datetime import datetime, time, timedelta

from app.auth import hash_password
from app.enums import Role
from app.models import Availability, User


def _aligned_future_slot() -> datetime:
    """A valid start: tomorrow (or the next working day) at 10:00, on the grid."""
    d = datetime.now() + timedelta(days=1)
    while d.weekday() == 6:
        d += timedelta(days=1)
    return d.replace(hour=10, minute=0, second=0, microsecond=0)


def _with_availability(db, doctor, slot):
    """Give the doctor a wide slot (08:00-18:00) on the day of the appointment."""
    dia = (slot.weekday() + 1) % 7
    db.add(
        Availability(
            usuario_id=doctor.id, dia_semana=dia, hora_inicio=time(8, 0), hora_fin=time(18, 0)
        )
    )
    db.flush()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_openapi_accessible(client):
    assert client.get("/openapi.json").status_code == 200


def test_login_ok_and_me(client, db):
    u = User(
        nombre_completo="Admin Login",
        rol=Role.ADMIN,
        email=f"login-{uuid.uuid4()}@test.local",
        password_hash=hash_password("secret123"),
    )
    db.add(u)
    db.flush()
    r = client.post("/auth/login", json={"email": u.email, "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["rol"] == "ADMIN"


def test_login_wrong_password(client, db):
    u = User(
        nombre_completo="Admin Malo",
        rol=Role.ADMIN,
        email=f"malo-{uuid.uuid4()}@test.local",
        password_hash=hash_password("secret123"),
    )
    db.add(u)
    db.flush()
    r = client.post("/auth/login", json={"email": u.email, "password": "incorrecta"})
    assert r.status_code == 401


def test_me_without_token(client):
    assert client.get("/auth/me").status_code in (401, 403)


def test_reception_cannot_see_users(client, recepcion, token_for):
    assert client.get("/usuarios", headers=token_for(recepcion)).status_code == 403


def test_admin_sees_users(client, admin, token_for):
    assert client.get("/usuarios", headers=token_for(admin)).status_code == 200


def test_doctor_cannot_cancel(client, doctor, token_for):
    r = client.post(f"/citas/{uuid.uuid4()}/cancelar", headers=token_for(doctor))
    assert r.status_code == 403


def test_doctor_cannot_mark_attendance(client, doctor, token_for):
    r = client.post(
        f"/citas/{uuid.uuid4()}/asistencia",
        headers=token_for(doctor),
        json={"estado": "COMPLETED"},
    )
    assert r.status_code == 403


def test_doctor_cannot_create_appointment(client, doctor, token_for):
    assert client.post("/citas", headers=token_for(doctor), json={}).status_code == 403


def test_doctor_sees_own_agenda(client, doctor, token_for):
    fecha = datetime.now().strftime("%Y-%m-%d")
    r = client.get(f"/citas?fecha={fecha}", headers=token_for(doctor))
    assert r.status_code == 200


def test_full_appointment_flow(client, db, admin, doctor, service, token_for):
    slot = _aligned_future_slot()
    _with_availability(db, doctor, slot)
    hdr = token_for(admin)
    body = {
        "nombre_completo": f"Integración {uuid.uuid4()}",
        "edad": 40,
        "medico_id": str(doctor.id),
        "servicio_id": str(service.id),
        "starts_at": slot.strftime("%Y-%m-%dT%H:%M:%S"),
        "duracion_min": 30,
    }
    r = client.post("/citas", headers=hdr, json=body)
    assert r.status_code == 201, r.text
    appointment = r.json()
    assert appointment["starts_at"].startswith(slot.strftime("%Y-%m-%dT%H:%M"))
    cita_id = appointment["id"]

    fecha = slot.strftime("%Y-%m-%d")
    lista = client.get(f"/citas?fecha={fecha}", headers=hdr).json()
    assert any(c["id"] == cita_id for c in lista)

    mov = client.put(
        f"/citas/{cita_id}",
        headers=hdr,
        json={"starts_at": slot.replace(hour=11).strftime("%Y-%m-%dT%H:%M:%S")},
    )
    assert mov.status_code == 200 and mov.json()["starts_at"].endswith("11:00:00")

    canc = client.post(f"/citas/{cita_id}/cancelar", headers=hdr)
    assert canc.status_code == 200 and canc.json()["estado"] == "CANCELLED"


def test_appointment_tzaware_date_rejected(client, db, admin, doctor, service, token_for):
    """Contract: a date carrying a timezone (the browser's 'Z') is rejected with 422."""
    slot = _aligned_future_slot()
    _with_availability(db, doctor, slot)
    body = {
        "nombre_completo": f"TZ {uuid.uuid4()}",
        "edad": 30,
        "medico_id": str(doctor.id),
        "servicio_id": str(service.id),
        "starts_at": slot.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        "duracion_min": 15,
    }
    r = client.post("/citas", headers=token_for(admin), json=body)
    assert r.status_code == 422, r.text


def test_appointment_ambiguous_patient_returns_candidates(
    client, db, admin, doctor, service, token_for
):
    slot = _aligned_future_slot()
    _with_availability(db, doctor, slot)
    nombre = f"Ambiguo {uuid.uuid4()}"
    db.add(User(nombre_completo=nombre, edad=50, rol=Role.PACIENTE))
    db.add(User(nombre_completo=nombre, edad=50, rol=Role.PACIENTE))
    db.flush()
    body = {
        "nombre_completo": nombre,
        "edad": 50,
        "medico_id": str(doctor.id),
        "servicio_id": str(service.id),
        "starts_at": slot.strftime("%Y-%m-%dT%H:%M:%S"),
        "duracion_min": 30,
    }
    r = client.post("/citas", headers=token_for(admin), json=body)
    assert r.status_code == 409
    candidates = r.json()["detail"]["candidatos"]
    assert len(candidates) == 2
    assert {"id", "nombre_completo", "edad"} <= set(candidates[0].keys())
