"""Tests del upsert de paciente (R1)."""

import uuid

import pytest

from app.models import Rol, Usuario
from app.services.pacientes import PacientesAmbiguos, buscar_o_crear_paciente


def test_crea_si_no_existe(db):
    nombre = f"Paciente {uuid.uuid4()}"
    p = buscar_o_crear_paciente(db, nombre, 40)
    assert p.id is not None
    assert p.rol == Rol.PACIENTE
    assert p.nombre_completo == nombre


def test_reutiliza_si_existe(db):
    nombre = f"Paciente {uuid.uuid4()}"
    p1 = buscar_o_crear_paciente(db, nombre, 30)
    p2 = buscar_o_crear_paciente(db, nombre, 30)
    assert p1.id == p2.id  # el mismo, no un duplicado


def test_varios_coinciden_lanza_ambiguo(db):
    nombre = f"Paciente {uuid.uuid4()}"
    db.add(Usuario(nombre_completo=nombre, edad=50, rol=Rol.PACIENTE))
    db.add(Usuario(nombre_completo=nombre, edad=50, rol=Rol.PACIENTE))
    db.flush()
    with pytest.raises(PacientesAmbiguos):
        buscar_o_crear_paciente(db, nombre, 50)
