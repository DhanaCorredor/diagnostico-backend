"""Tests del catálogo: lecturas y gestión (servicios, especialidades, médicos)."""

import uuid

import pytest

from app.enums import Role, ServiceCategory
from app.models import Specialty, Service, User
from app.services import catalogo as C


def test_listar_servicios_solo_activos_y_ordenados(db):
    activo_b = Service(nombre=f"B {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA)
    activo_a = Service(nombre=f"A {uuid.uuid4()}", categoria=ServiceCategory.ECOGRAFIA)
    inactivo = Service(
        nombre=f"Z {uuid.uuid4()}", categoria=ServiceCategory.OTRO, activo=False
    )
    db.add_all([activo_b, activo_a, inactivo])
    db.flush()

    nombres = [s.nombre for s in C.list_services(db)]
    assert activo_a.nombre in nombres and activo_b.nombre in nombres
    assert inactivo.nombre not in nombres
    assert nombres.index(activo_a.nombre) < nombres.index(activo_b.nombre)


def test_listar_servicios_filtra_por_medico(db):
    cardio = Specialty(nombre=f"Cardio {uuid.uuid4()}")
    derma = Specialty(nombre=f"Derma {uuid.uuid4()}")
    doctor = User(
        nombre_completo=f"Dr. Cardio {uuid.uuid4()}", rol=Role.MEDICO, especialidades=[cardio]
    )
    serv_cardio = Service(nombre=f"Eco cardíaca {uuid.uuid4()}", categoria=ServiceCategory.ESTUDIO_CARDIACO)
    serv_cardio.especialidades = [cardio]
    serv_derma = Service(nombre=f"Consulta piel {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA)
    serv_derma.especialidades = [derma]
    db.add_all([cardio, derma, doctor, serv_cardio, serv_derma])
    db.flush()

    ids = [s.id for s in C.list_services(db, doctor.id)]
    assert serv_cardio.id in ids
    assert serv_derma.id not in ids


def test_listar_medicos_activos_con_especialidades(db):
    esp = Specialty(nombre=f"Cardio {uuid.uuid4()}")
    activo = User(
        nombre_completo=f"Dr. Activo {uuid.uuid4()}", rol=Role.MEDICO, especialidades=[esp]
    )
    inactivo = User(nombre_completo=f"Dr. Baja {uuid.uuid4()}", rol=Role.MEDICO, activo=False)
    patient = User(nombre_completo=f"Paciente {uuid.uuid4()}", rol=Role.PACIENTE)
    db.add_all([esp, activo, inactivo, patient])
    db.flush()

    medicos = C.list_doctors(db)
    ids = [m.id for m in medicos]
    assert activo.id in ids
    assert inactivo.id not in ids
    assert patient.id not in ids
    m = next(x for x in medicos if x.id == activo.id)
    assert esp.nombre in [e.nombre for e in m.especialidades]


def test_listar_especialidades_ordenadas(db):
    e_a = Specialty(nombre=f"A {uuid.uuid4()}")
    e_z = Specialty(nombre=f"Z {uuid.uuid4()}")
    db.add_all([e_z, e_a])
    db.flush()
    nombres = [e.nombre for e in C.list_specialties(db)]
    assert e_a.nombre in nombres and e_z.nombre in nombres
    assert nombres.index(e_a.nombre) < nombres.index(e_z.nombre)


def test_crear_servicio(db):
    service = C.create_service(
        db, nombre=f"Ecografía {uuid.uuid4()}", categoria=ServiceCategory.ECOGRAFIA
    )
    assert service.id is not None
    assert service.activo is True


def test_crear_servicio_nombre_duplicado(db):
    nombre = f"Repetido {uuid.uuid4()}"
    C.create_service(db, nombre=nombre, categoria=ServiceCategory.CONSULTA)
    with pytest.raises(C.DuplicateName):
        C.create_service(db, nombre=nombre, categoria=ServiceCategory.OTRO)


def test_actualizar_servicio_cambia_campos(db):
    service = C.create_service(
        db, nombre=f"Viejo {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA
    )
    nuevo_nombre = f"Nuevo {uuid.uuid4()}"
    C.update_service(
        db, service.id, {"nombre": nuevo_nombre, "categoria": ServiceCategory.OTRO}
    )
    assert service.nombre == nuevo_nombre
    assert service.categoria == ServiceCategory.OTRO


def test_actualizar_servicio_desactiva(db):
    service = C.create_service(
        db, nombre=f"Baja {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA
    )
    C.update_service(db, service.id, {"activo": False})
    assert service.activo is False
    assert service.id not in [s.id for s in C.list_services(db)]


def test_actualizar_servicio_inexistente(db):
    with pytest.raises(C.ServiceNotFound):
        C.update_service(db, uuid.uuid4(), {"nombre": "x"})


def test_actualizar_servicio_nombre_duplicado(db):
    a = C.create_service(db, nombre=f"A {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA)
    b = C.create_service(db, nombre=f"B {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA)
    with pytest.raises(C.DuplicateName):
        C.update_service(db, b.id, {"nombre": a.nombre})


def test_actualizar_servicio_mismo_nombre_no_choca(db):
    service = C.create_service(
        db, nombre=f"Igual {uuid.uuid4()}", categoria=ServiceCategory.CONSULTA
    )
    C.update_service(db, service.id, {"nombre": service.nombre})
    assert service.activo is True


def test_crear_especialidad(db):
    esp = C.create_specialty(db, nombre=f"Neurología {uuid.uuid4()}")
    assert esp.id is not None


def test_crear_especialidad_nombre_duplicado(db):
    nombre = f"Cardiología {uuid.uuid4()}"
    C.create_specialty(db, nombre=nombre)
    with pytest.raises(C.DuplicateName):
        C.create_specialty(db, nombre=nombre)
