"""Tests del upsert de paciente (R1)."""

import uuid

import pytest

from app.enums import Rol
from app.models import Usuario
from app.services.pacientes import (
    CedulaDuplicada,
    PacienteNoEncontrado,
    PacientesAmbiguos,
    actualizar_paciente,
    buscar_o_crear_paciente,
    crear_paciente,
    desactivar_paciente,
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
    assert p1.id == p2.id


def test_varios_coinciden_lanza_ambiguo(db):
    nombre = f"Paciente {uuid.uuid4()}"
    db.add(Usuario(nombre_completo=nombre, edad=50, rol=Rol.PACIENTE))
    db.add(Usuario(nombre_completo=nombre, edad=50, rol=Rol.PACIENTE))
    db.flush()
    with pytest.raises(PacientesAmbiguos) as exc:
        buscar_o_crear_paciente(db, nombre, 50)
    assert len(exc.value.candidatos) == 2


def test_listar_pacientes_solo_pacientes(db):
    pac = Usuario(nombre_completo=f"Pac {uuid.uuid4()}", edad=40, rol=Rol.PACIENTE)
    medico = Usuario(nombre_completo=f"Dr {uuid.uuid4()}", rol=Rol.MEDICO)
    db.add_all([pac, medico])
    db.flush()
    ids = [p.id for p in listar_pacientes(db)]
    assert pac.id in ids
    assert medico.id not in ids


def test_obtener_paciente_ok_y_no_encontrado(db):
    pac = Usuario(nombre_completo=f"Pac {uuid.uuid4()}", edad=40, rol=Rol.PACIENTE)
    db.add(pac)
    db.flush()
    assert obtener_paciente(db, pac.id).id == pac.id
    with pytest.raises(PacienteNoEncontrado):
        obtener_paciente(db, uuid.uuid4())


def test_actualizar_paciente(db):
    pac = buscar_o_crear_paciente(db, f"Pac {uuid.uuid4()}", 40)
    actualizado = actualizar_paciente(db, pac.id, {"nombre_completo": "Nuevo Nombre", "edad": 41})
    assert actualizado.nombre_completo == "Nuevo Nombre"
    assert actualizado.edad == 41


def test_actualizar_paciente_parcial_no_borra_cedula(db):
    pac = buscar_o_crear_paciente(db, f"Pac {uuid.uuid4()}", 40)
    pac.cedula = f"V-{uuid.uuid4()}"
    db.flush()
    ced_original = pac.cedula
    actualizar_paciente(db, pac.id, {"telefono": "555-9999"})
    assert pac.cedula == ced_original
    assert pac.telefono == "555-9999"


def test_crear_paciente_alta_manual(db):
    datos = {
        "nombre_completo": f"Pac {uuid.uuid4()}",
        "edad": 33,
        "cedula": None,
        "telefono": None,
        "fecha_nacimiento": None,
    }
    p = crear_paciente(db, datos)
    assert p.id is not None
    assert p.rol == Rol.PACIENTE
    assert p.edad == 33


def test_crear_paciente_cedula_duplicada(db):
    ced = f"CED-{uuid.uuid4()}"
    db.add(Usuario(nombre_completo=f"Otro {uuid.uuid4()}", edad=30, rol=Rol.PACIENTE, cedula=ced))
    db.flush()
    with pytest.raises(CedulaDuplicada):
        crear_paciente(
            db,
            {"nombre_completo": "X", "edad": 20, "cedula": ced, "telefono": None, "fecha_nacimiento": None},
        )


def test_actualizar_paciente_cedula_duplicada(db):
    ced = f"CED-{uuid.uuid4()}"
    otro = Usuario(nombre_completo=f"Otro {uuid.uuid4()}", edad=30, rol=Rol.PACIENTE, cedula=ced)
    db.add(otro)
    db.flush()
    pac = buscar_o_crear_paciente(db, f"Pac {uuid.uuid4()}", 40)
    with pytest.raises(CedulaDuplicada):
        actualizar_paciente(db, pac.id, {"cedula": ced})


def test_desactivar_paciente_baja_logica(db):
    pac = buscar_o_crear_paciente(db, f"Pac {uuid.uuid4()}", 40)
    desactivado = desactivar_paciente(db, pac.id)
    assert desactivado.activo is False
    assert pac.id not in [p.id for p in listar_pacientes(db)]
