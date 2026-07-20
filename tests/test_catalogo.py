"""Tests de las lecturas de catálogo (servicios, especialidades, médicos)."""

import uuid

from app.models import Especialidad, Rol, Servicio, ServicioCategoria, Usuario
from app.services import catalogo as C


def test_listar_servicios_solo_activos_y_ordenados(db):
    # dos activos (con nombres desordenados) y uno inactivo
    activo_b = Servicio(nombre=f"B {uuid.uuid4()}", categoria=ServicioCategoria.CONSULTA)
    activo_a = Servicio(nombre=f"A {uuid.uuid4()}", categoria=ServicioCategoria.ECOGRAFIA)
    inactivo = Servicio(
        nombre=f"Z {uuid.uuid4()}", categoria=ServicioCategoria.OTRO, activo=False
    )
    db.add_all([activo_b, activo_a, inactivo])
    db.flush()

    nombres = [s.nombre for s in C.listar_servicios(db)]
    assert activo_a.nombre in nombres and activo_b.nombre in nombres
    assert inactivo.nombre not in nombres          # los inactivos no salen
    # ordenados por nombre: 'A...' aparece antes que 'B...'
    assert nombres.index(activo_a.nombre) < nombres.index(activo_b.nombre)


def test_listar_medicos_activos_con_especialidades(db):
    esp = Especialidad(nombre=f"Cardio {uuid.uuid4()}")
    activo = Usuario(
        nombre_completo=f"Dr. Activo {uuid.uuid4()}", rol=Rol.MEDICO, especialidades=[esp]
    )
    inactivo = Usuario(nombre_completo=f"Dr. Baja {uuid.uuid4()}", rol=Rol.MEDICO, activo=False)
    paciente = Usuario(nombre_completo=f"Paciente {uuid.uuid4()}", rol=Rol.PACIENTE)
    db.add_all([esp, activo, inactivo, paciente])
    db.flush()

    medicos = C.listar_medicos(db)
    ids = [m.id for m in medicos]
    assert activo.id in ids            # médico activo -> sí
    assert inactivo.id not in ids      # médico dado de baja -> no
    assert paciente.id not in ids      # un paciente -> no
    # trae sus especialidades
    m = next(x for x in medicos if x.id == activo.id)
    assert esp.nombre in [e.nombre for e in m.especialidades]
