"""Tests del catálogo: lecturas y gestión (servicios, especialidades, médicos)."""

import uuid

import pytest

from app.models import Especialidad, Rol, Servicio, ServicioCategoria, Usuario
from app.services import catalogo as C


def test_listar_servicios_solo_activos_y_ordenados(db):
    activo_b = Servicio(nombre=f"B {uuid.uuid4()}", categoria=ServicioCategoria.CONSULTA)
    activo_a = Servicio(nombre=f"A {uuid.uuid4()}", categoria=ServicioCategoria.ECOGRAFIA)
    inactivo = Servicio(
        nombre=f"Z {uuid.uuid4()}", categoria=ServicioCategoria.OTRO, activo=False
    )
    db.add_all([activo_b, activo_a, inactivo])
    db.flush()

    nombres = [s.nombre for s in C.listar_servicios(db)]
    assert activo_a.nombre in nombres and activo_b.nombre in nombres
    assert inactivo.nombre not in nombres
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
    assert activo.id in ids
    assert inactivo.id not in ids
    assert paciente.id not in ids
    m = next(x for x in medicos if x.id == activo.id)
    assert esp.nombre in [e.nombre for e in m.especialidades]


def test_listar_especialidades_ordenadas(db):
    e_a = Especialidad(nombre=f"A {uuid.uuid4()}")
    e_z = Especialidad(nombre=f"Z {uuid.uuid4()}")
    db.add_all([e_z, e_a])
    db.flush()
    nombres = [e.nombre for e in C.listar_especialidades(db)]
    assert e_a.nombre in nombres and e_z.nombre in nombres
    assert nombres.index(e_a.nombre) < nombres.index(e_z.nombre)


def test_crear_servicio(db):
    servicio = C.crear_servicio(
        db, nombre=f"Ecografía {uuid.uuid4()}", categoria=ServicioCategoria.ECOGRAFIA
    )
    assert servicio.id is not None
    assert servicio.activo is True


def test_crear_servicio_nombre_duplicado(db):
    nombre = f"Repetido {uuid.uuid4()}"
    C.crear_servicio(db, nombre=nombre, categoria=ServicioCategoria.CONSULTA)
    with pytest.raises(C.NombreDuplicado):
        C.crear_servicio(db, nombre=nombre, categoria=ServicioCategoria.OTRO)


def test_actualizar_servicio_cambia_campos(db):
    servicio = C.crear_servicio(
        db, nombre=f"Viejo {uuid.uuid4()}", categoria=ServicioCategoria.CONSULTA
    )
    nuevo_nombre = f"Nuevo {uuid.uuid4()}"
    C.actualizar_servicio(
        db, servicio.id, {"nombre": nuevo_nombre, "categoria": ServicioCategoria.OTRO}
    )
    assert servicio.nombre == nuevo_nombre
    assert servicio.categoria == ServicioCategoria.OTRO


def test_actualizar_servicio_desactiva(db):
    servicio = C.crear_servicio(
        db, nombre=f"Baja {uuid.uuid4()}", categoria=ServicioCategoria.CONSULTA
    )
    C.actualizar_servicio(db, servicio.id, {"activo": False})
    assert servicio.activo is False
    assert servicio.id not in [s.id for s in C.listar_servicios(db)]


def test_actualizar_servicio_inexistente(db):
    with pytest.raises(C.ServicioNoEncontrado):
        C.actualizar_servicio(db, uuid.uuid4(), {"nombre": "x"})


def test_actualizar_servicio_nombre_duplicado(db):
    a = C.crear_servicio(db, nombre=f"A {uuid.uuid4()}", categoria=ServicioCategoria.CONSULTA)
    b = C.crear_servicio(db, nombre=f"B {uuid.uuid4()}", categoria=ServicioCategoria.CONSULTA)
    with pytest.raises(C.NombreDuplicado):
        C.actualizar_servicio(db, b.id, {"nombre": a.nombre})


def test_actualizar_servicio_mismo_nombre_no_choca(db):
    servicio = C.crear_servicio(
        db, nombre=f"Igual {uuid.uuid4()}", categoria=ServicioCategoria.CONSULTA
    )
    C.actualizar_servicio(db, servicio.id, {"nombre": servicio.nombre})
    assert servicio.activo is True


def test_crear_especialidad(db):
    esp = C.crear_especialidad(db, nombre=f"Neurología {uuid.uuid4()}")
    assert esp.id is not None


def test_crear_especialidad_nombre_duplicado(db):
    nombre = f"Cardiología {uuid.uuid4()}"
    C.crear_especialidad(db, nombre=nombre)
    with pytest.raises(C.NombreDuplicado):
        C.crear_especialidad(db, nombre=nombre)
