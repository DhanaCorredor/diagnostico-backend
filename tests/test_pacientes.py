"""Tests del upsert de paciente (R1)."""

import uuid

import pytest

from app.models import Rol, Usuario
from app.services.pacientes import (
    CedulaDuplicada,
    PacienteNoEncontrado,
    PacientesAmbiguos,
    actualizar_paciente,
    buscar_o_crear_paciente,
    listar_pacientes,
    obtener_paciente,
)


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


# --- Gestión de pacientes (listar / ver / editar) ---------------------------


def test_listar_pacientes_solo_pacientes(db):
    pac = Usuario(nombre_completo=f"Pac {uuid.uuid4()}", edad=40, rol=Rol.PACIENTE)
    medico = Usuario(nombre_completo=f"Dr {uuid.uuid4()}", rol=Rol.MEDICO)
    db.add_all([pac, medico])
    db.flush()
    ids = [p.id for p in listar_pacientes(db)]
    assert pac.id in ids
    assert medico.id not in ids  # los médicos no son pacientes


def test_obtener_paciente_ok_y_no_encontrado(db):
    pac = Usuario(nombre_completo=f"Pac {uuid.uuid4()}", edad=40, rol=Rol.PACIENTE)
    db.add(pac)
    db.flush()
    assert obtener_paciente(db, pac.id).id == pac.id
    with pytest.raises(PacienteNoEncontrado):
        obtener_paciente(db, uuid.uuid4())


def test_actualizar_paciente(db):
    pac = buscar_o_crear_paciente(db, f"Pac {uuid.uuid4()}", 40)
    actualizado = actualizar_paciente(
        db,
        pac.id,
        nombre_completo="Nuevo Nombre",
        edad=41,
        cedula=f"CED-{uuid.uuid4()}",
        telefono="12345",
        fecha_nacimiento=None,
    )
    assert actualizado.nombre_completo == "Nuevo Nombre"
    assert actualizado.edad == 41


def test_actualizar_paciente_cedula_duplicada(db):
    ced = f"CED-{uuid.uuid4()}"
    otro = Usuario(nombre_completo=f"Otro {uuid.uuid4()}", edad=30, rol=Rol.PACIENTE, cedula=ced)
    db.add(otro)
    db.flush()
    pac = buscar_o_crear_paciente(db, f"Pac {uuid.uuid4()}", 40)
    with pytest.raises(CedulaDuplicada):
        actualizar_paciente(
            db,
            pac.id,
            nombre_completo="X",
            edad=40,
            cedula=ced,
            telefono=None,
            fecha_nacimiento=None,
        )
