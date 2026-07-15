"""Tests de las reglas de citas (R2, R3, R4) y del orquestador crear_cita."""

import uuid
from datetime import datetime, time

import pytest

from app.models import Cita, Disponibilidad, EstadoCita, Rol, Usuario
from app.services import citas as C

# Un lunes cualquiera, y su día en la convención del modelo (0=domingo).
LUNES_10 = datetime(2026, 7, 20, 10, 0)
DIA_LUNES = (LUNES_10.weekday() + 1) % 7


def _franja(db, medico, hora_inicio=time(8, 0), hora_fin=time(14, 0)):
    db.add(
        Disponibilidad(
            usuario_id=medico.id,
            dia_semana=DIA_LUNES,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        )
    )
    db.flush()


# --- R2: duración ------------------------------------------------------------


def test_calcular_ends_at(servicio):
    fin = C.calcular_ends_at(datetime(2026, 7, 20, 10, 0), servicio)
    assert fin == datetime(2026, 7, 20, 10, 45)  # servicio de 45 min


# --- R3: disponibilidad ------------------------------------------------------


def test_disponibilidad_dentro_y_fuera(db, medico):
    _franja(db, medico)  # lunes 08:00-14:00
    dentro = C.dentro_de_disponibilidad(
        db, medico.id, datetime(2026, 7, 20, 10, 0), datetime(2026, 7, 20, 10, 45)
    )
    fuera = C.dentro_de_disponibilidad(
        db, medico.id, datetime(2026, 7, 20, 7, 0), datetime(2026, 7, 20, 7, 45)
    )
    assert dentro is True
    assert fuera is False


# --- R4: anti-solapamiento ---------------------------------------------------


def test_solapamiento_y_citas_pegadas(db, medico, servicio, admin):
    pac = Usuario(nombre_completo=f"P {uuid.uuid4()}", edad=1, rol=Rol.PACIENTE)
    db.add(pac)
    db.flush()
    db.add(
        Cita(
            paciente_id=pac.id,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=datetime(2026, 7, 20, 10, 0),
            ends_at=datetime(2026, 7, 20, 10, 45),
            estado=EstadoCita.SCHEDULED,
            creado_por_id=admin.id,
        )
    )
    db.flush()
    # se cruza -> True
    assert C.hay_solapamiento(
        db, medico.id, datetime(2026, 7, 20, 10, 30), datetime(2026, 7, 20, 11, 0)
    ) is True
    # pegada justo después -> False (se permite)
    assert C.hay_solapamiento(
        db, medico.id, datetime(2026, 7, 20, 10, 45), datetime(2026, 7, 20, 11, 30)
    ) is False


# --- Orquestador crear_cita --------------------------------------------------


def test_crear_cita_feliz(db, medico, servicio, admin):
    _franja(db, medico)
    cita = C.crear_cita(
        db,
        nombre_completo=f"Ana {uuid.uuid4()}",
        edad=33,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=LUNES_10,
        creado_por_id=admin.id,
    )
    assert cita.ends_at == datetime(2026, 7, 20, 10, 45)
    assert cita.estado == EstadoCita.SCHEDULED


def test_crear_cita_fuera_de_disponibilidad(db, medico, servicio, admin):
    # sin franja -> cualquier hora está fuera
    with pytest.raises(C.FueraDeDisponibilidad):
        C.crear_cita(
            db,
            nombre_completo=f"X {uuid.uuid4()}",
            edad=1,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=LUNES_10,
            creado_por_id=admin.id,
        )


def test_crear_cita_bloquea_solapamiento(db, medico, servicio, admin):
    _franja(db, medico)
    C.crear_cita(
        db,
        nombre_completo=f"A {uuid.uuid4()}",
        edad=1,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=LUNES_10,
        creado_por_id=admin.id,
    )
    with pytest.raises(C.Solapamiento):
        C.crear_cita(
            db,
            nombre_completo=f"B {uuid.uuid4()}",
            edad=2,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=datetime(2026, 7, 20, 10, 30),
            creado_por_id=admin.id,
        )


def test_crear_cita_medico_invalido(db, servicio, admin):
    # admin no tiene rol MEDICO
    with pytest.raises(C.MedicoNoEncontrado):
        C.crear_cita(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=admin.id,
            servicio_id=servicio.id,
            starts_at=LUNES_10,
            creado_por_id=admin.id,
        )


def test_crear_cita_servicio_invalido(db, medico, admin):
    with pytest.raises(C.ServicioNoEncontrado):
        C.crear_cita(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=medico.id,
            servicio_id=uuid.uuid4(),
            starts_at=LUNES_10,
            creado_por_id=admin.id,
        )
