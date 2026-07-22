"""Tests de integración HTTP (TestClient): auth, guardas por rol y flujo de citas.

Cubren la capa que los tests de servicio NO tocan: autenticación, dependencias
por rol, serialización y el contrato real de la API de punta a punta. Portados
del smoke test manual para que queden repetibles y en CI.
"""

import uuid
from datetime import datetime, time, timedelta

from app.auth import hashear_password
from app.models import Disponibilidad, Rol, Usuario


def _slot_futuro_alineado() -> datetime:
    """Un inicio válido: mañana (o el siguiente día laborable) a las 10:00, en rejilla."""
    d = datetime.now() + timedelta(days=1)
    while d.weekday() == 6:  # domingo cerrado (weekday: lunes=0 ... domingo=6)
        d += timedelta(days=1)
    return d.replace(hour=10, minute=0, second=0, microsecond=0)


def _con_disponibilidad(db, medico, slot):
    """Da al médico una franja amplia (08:00-18:00) el día del slot."""
    dia = (slot.weekday() + 1) % 7  # convención del modelo: domingo=0
    db.add(
        Disponibilidad(
            usuario_id=medico.id, dia_semana=dia, hora_inicio=time(8, 0), hora_fin=time(18, 0)
        )
    )
    db.flush()


# --- Salud / OpenAPI ---------------------------------------------------------


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_openapi_accesible(client):
    assert client.get("/openapi.json").status_code == 200


# --- Autenticación -----------------------------------------------------------


def test_login_ok_y_me(client, db):
    u = Usuario(
        nombre_completo="Admin Login",
        rol=Rol.ADMIN,
        email=f"login-{uuid.uuid4()}@test.local",
        password_hash=hashear_password("secret123"),
    )
    db.add(u)
    db.flush()
    r = client.post("/auth/login", json={"email": u.email, "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["rol"] == "ADMIN"


def test_login_password_mala(client, db):
    u = Usuario(
        nombre_completo="Admin Malo",
        rol=Rol.ADMIN,
        email=f"malo-{uuid.uuid4()}@test.local",
        password_hash=hashear_password("secret123"),
    )
    db.add(u)
    db.flush()
    r = client.post("/auth/login", json={"email": u.email, "password": "incorrecta"})
    assert r.status_code == 401


def test_me_sin_token(client):
    assert client.get("/auth/me").status_code in (401, 403)


# --- Guardas por rol ---------------------------------------------------------


def test_recepcion_no_ve_usuarios(client, recepcion, token_for):
    assert client.get("/usuarios", headers=token_for(recepcion)).status_code == 403


def test_admin_si_ve_usuarios(client, admin, token_for):
    assert client.get("/usuarios", headers=token_for(admin)).status_code == 200


def test_medico_no_cancela(client, medico, token_for):
    r = client.post(f"/citas/{uuid.uuid4()}/cancelar", headers=token_for(medico))
    assert r.status_code == 403


def test_medico_no_marca_asistencia(client, medico, token_for):
    r = client.post(
        f"/citas/{uuid.uuid4()}/asistencia",
        headers=token_for(medico),
        json={"estado": "COMPLETED"},
    )
    assert r.status_code == 403


def test_medico_no_crea_cita(client, medico, token_for):
    assert client.post("/citas", headers=token_for(medico), json={}).status_code == 403


def test_medico_ve_su_agenda(client, medico, token_for):
    fecha = datetime.now().strftime("%Y-%m-%d")
    r = client.get(f"/citas?fecha={fecha}", headers=token_for(medico))
    assert r.status_code == 200


# --- Flujo completo de una cita + validador de fechas (Z) --------------------


def test_flujo_cita_completo(client, db, admin, medico, servicio, token_for):
    slot = _slot_futuro_alineado()
    _con_disponibilidad(db, medico, slot)
    hdr = token_for(admin)
    body = {
        "nombre_completo": f"Integración {uuid.uuid4()}",
        "edad": 40,
        "medico_id": str(medico.id),
        "servicio_id": str(servicio.id),
        "starts_at": slot.strftime("%Y-%m-%dT%H:%M:%S") + "Z",  # 'Z' -> prueba el validador
        "duracion_min": 30,
    }
    r = client.post("/citas", headers=hdr, json=body)
    assert r.status_code == 201, r.text
    cita = r.json()
    # el validador normaliza la 'Z' a hora local: se guarda 10:00 tal cual
    assert cita["starts_at"].startswith(slot.strftime("%Y-%m-%dT%H:%M"))
    cita_id = cita["id"]

    # aparece en la agenda del día
    fecha = slot.strftime("%Y-%m-%d")
    lista = client.get(f"/citas?fecha={fecha}", headers=hdr).json()
    assert any(c["id"] == cita_id for c in lista)

    # mover a las 11:00
    mov = client.put(
        f"/citas/{cita_id}",
        headers=hdr,
        json={"starts_at": slot.replace(hour=11).strftime("%Y-%m-%dT%H:%M:%S")},
    )
    assert mov.status_code == 200 and mov.json()["starts_at"].endswith("11:00:00")

    # cancelar libera el cupo
    canc = client.post(f"/citas/{cita_id}/cancelar", headers=hdr)
    assert canc.status_code == 200 and canc.json()["estado"] == "CANCELLED"


def test_cita_fecha_con_zona_no_da_500(client, db, admin, medico, servicio, token_for):
    """La 'Z' del navegador no debe provocar un 500 (bug naive/aware corregido)."""
    slot = _slot_futuro_alineado()
    _con_disponibilidad(db, medico, slot)
    body = {
        "nombre_completo": f"TZ {uuid.uuid4()}",
        "edad": 30,
        "medico_id": str(medico.id),
        "servicio_id": str(servicio.id),
        "starts_at": slot.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        "duracion_min": 15,
    }
    r = client.post("/citas", headers=token_for(admin), json=body)
    assert r.status_code == 201, r.text  # 201, no 500


# --- 409 de paciente ambiguo con candidatos ----------------------------------


def test_cita_paciente_ambiguo_devuelve_candidatos(
    client, db, admin, medico, servicio, token_for
):
    slot = _slot_futuro_alineado()
    _con_disponibilidad(db, medico, slot)
    nombre = f"Ambiguo {uuid.uuid4()}"
    db.add(Usuario(nombre_completo=nombre, edad=50, rol=Rol.PACIENTE))
    db.add(Usuario(nombre_completo=nombre, edad=50, rol=Rol.PACIENTE))
    db.flush()
    body = {
        "nombre_completo": nombre,
        "edad": 50,
        "medico_id": str(medico.id),
        "servicio_id": str(servicio.id),
        "starts_at": slot.strftime("%Y-%m-%dT%H:%M:%S"),
        "duracion_min": 30,
    }
    r = client.post("/citas", headers=token_for(admin), json=body)
    assert r.status_code == 409
    candidatos = r.json()["detail"]["candidatos"]
    assert len(candidatos) == 2
    assert {"id", "nombre_completo", "edad"} <= set(candidatos[0].keys())
