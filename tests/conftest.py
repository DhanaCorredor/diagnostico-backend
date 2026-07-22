"""Configuración común de los tests: sesión de BD aislada y datos de apoyo.

Cada test corre dentro de una transacción que se revierte al terminar (rollback),
así las pruebas no dejan rastro en la base de datos.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth import crear_token
from app.db import SessionLocal, engine, get_db
from app.main import app
from app.models import Rol, Servicio, ServicioCategoria, Usuario


@pytest.fixture
def db():
    """Sesión envuelta en una transacción que se revierte al final del test.

    `join_transaction_mode="create_savepoint"`: los `commit()` que hacen los
    endpoints (en los tests de integración) se confinan a un SAVEPOINT, así el
    rollback final los deshace igual y nada queda en la base de datos.
    """
    connection = engine.connect()
    trans = connection.begin()
    session = SessionLocal(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture
def client(db):
    """TestClient con la BD de test inyectada: la app usa la MISMA sesión que el test.

    Sobrescribe la dependencia `get_db` para que los endpoints compartan la
    transacción del test (que se revierte al final).
    """
    def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def token_for():
    """Devuelve una función que construye la cabecera Authorization de un usuario."""
    def _header(usuario):
        return {"Authorization": f"Bearer {crear_token(usuario.id)}"}

    return _header


@pytest.fixture
def medico(db):
    """Un médico de prueba (email único para no chocar con otros)."""
    m = Usuario(
        nombre_completo="Dr. Test",
        rol=Rol.MEDICO,
        email=f"med-{uuid.uuid4()}@test.local",
    )
    db.add(m)
    db.flush()
    return m


@pytest.fixture
def admin(db):
    """Un admin de prueba (hace de 'creado_por' de las citas)."""
    a = Usuario(
        nombre_completo="Admin Test",
        rol=Rol.ADMIN,
        email=f"adm-{uuid.uuid4()}@test.local",
    )
    db.add(a)
    db.flush()
    return a


@pytest.fixture
def recepcion(db):
    """Un usuario de recepción de prueba (para los guardas por rol)."""
    r = Usuario(
        nombre_completo="Recep Test",
        rol=Rol.RECEPCION,
        email=f"rec-{uuid.uuid4()}@test.local",
    )
    db.add(r)
    db.flush()
    return r


@pytest.fixture
def servicio(db):
    """Un servicio de prueba del catálogo (nombre único)."""
    s = Servicio(
        nombre=f"Servicio {uuid.uuid4()}",
        categoria=ServicioCategoria.CONSULTA,
    )
    db.add(s)
    db.flush()
    return s
