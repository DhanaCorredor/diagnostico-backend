"""Tests de la gestión de personal/médicos (CRUD): crear, listar, ver, editar."""

import uuid

import pytest

from app.enums import Role
from app.models import Specialty, User
from app.services import usuarios as U


def _crear(db, **over):
    """Crea un usuario de personal con datos por defecto (médico), sobreescribibles."""
    base = dict(
        nombre_completo=f"Dr {uuid.uuid4()}",
        rol=Role.MEDICO,
        email=f"u-{uuid.uuid4()}@test.local",
        password="password123",
        matricula=None,
        especialidades=[],
    )
    base.update(over)
    return U.crear_usuario(db, **base)


def test_crear_usuario_hashea_password(db):
    u = _crear(db, rol=Role.RECEPCION)
    assert u.id is not None
    assert u.password_hash and u.password_hash != "password123"


def test_crear_medico_con_especialidades(db):
    esp = Specialty(nombre=f"Cardio {uuid.uuid4()}")
    db.add(esp)
    db.flush()
    u = _crear(db, rol=Role.MEDICO, especialidades=[esp.id])
    assert esp.id in [e.id for e in u.especialidades]


def test_crear_usuario_rol_paciente_no_permitido(db):
    with pytest.raises(U.RolNoPermitido):
        _crear(db, rol=Role.PACIENTE)


def test_crear_usuario_email_duplicado(db):
    email = f"dup-{uuid.uuid4()}@test.local"
    _crear(db, email=email)
    with pytest.raises(U.EmailDuplicado):
        _crear(db, email=email)


def test_crear_usuario_especialidad_inexistente(db):
    with pytest.raises(U.EspecialidadNoEncontrada):
        _crear(db, especialidades=[uuid.uuid4()])


def test_no_medico_con_especialidades_falla(db):
    esp = Specialty(nombre=f"E {uuid.uuid4()}")
    db.add(esp)
    db.flush()
    with pytest.raises(U.DatosSoloDeMedico):
        _crear(db, rol=Role.RECEPCION, especialidades=[esp.id])


def test_no_medico_con_matricula_falla(db):
    with pytest.raises(U.DatosSoloDeMedico):
        _crear(db, rol=Role.ADMIN, matricula="MAT-1")


def test_listar_personal_excluye_pacientes(db):
    med = _crear(db, rol=Role.MEDICO)
    pac = User(nombre_completo=f"Pac {uuid.uuid4()}", edad=30, rol=Role.PACIENTE)
    db.add(pac)
    db.flush()
    ids = [u.id for u in U.listar_personal(db)]
    assert med.id in ids
    assert pac.id not in ids


def test_obtener_usuario_no_encontrado(db):
    with pytest.raises(U.UsuarioNoEncontrado):
        U.obtener_usuario(db, uuid.uuid4())


def test_actualizar_usuario_parcial_no_toca_password(db):
    u = _crear(db, rol=Role.RECEPCION)
    hash_original = u.password_hash
    U.actualizar_usuario(db, u.id, {"nombre_completo": "Nuevo"})
    assert u.nombre_completo == "Nuevo"
    assert u.password_hash == hash_original


def test_actualizar_usuario_cambia_password(db):
    u = _crear(db, rol=Role.RECEPCION)
    hash_original = u.password_hash
    U.actualizar_usuario(db, u.id, {"password": "nuevopass1"})
    assert u.password_hash != hash_original


def test_actualizar_usuario_email_duplicado(db):
    otro = _crear(db, rol=Role.RECEPCION)
    u = _crear(db, rol=Role.MEDICO)
    with pytest.raises(U.EmailDuplicado):
        U.actualizar_usuario(db, u.id, {"email": otro.email})


def test_actualizar_usuario_especialidades(db):
    esp = Specialty(nombre=f"Neuro {uuid.uuid4()}")
    db.add(esp)
    db.flush()
    u = _crear(db, rol=Role.MEDICO)
    U.actualizar_usuario(db, u.id, {"especialidades": [esp.id]})
    assert esp.id in [e.id for e in u.especialidades]


def test_actualizar_usuario_no_encontrado(db):
    with pytest.raises(U.UsuarioNoEncontrado):
        U.actualizar_usuario(db, uuid.uuid4(), {"nombre_completo": "X"})


def test_desactivar_usuario(db):
    u = _crear(db, rol=Role.MEDICO)
    assert u.activo is True
    U.desactivar_usuario(db, u.id)
    assert u.activo is False


def test_reactivar_usuario_por_put(db):
    u = _crear(db, rol=Role.MEDICO)
    U.desactivar_usuario(db, u.id)
    U.actualizar_usuario(db, u.id, {"activo": True})
    assert u.activo is True
