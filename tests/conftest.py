"""Configuración común de los tests: sesión de BD aislada y datos de apoyo.

Cada test corre dentro de una transacción que se revierte al terminar (rollback),
así las pruebas no dejan rastro en la base de datos.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth import create_token
from app.db import SessionLocal, engine, get_db
from app.main import app
from app.enums import Role, ServiceCategory
from app.models import Service, User


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
    def _header(user):
        return {"Authorization": f"Bearer {create_token(user.id)}"}

    return _header


@pytest.fixture
def doctor(db):
    """Un médico de prueba (email único para no chocar con otros)."""
    m = User(
        nombre_completo="Dr. Test",
        rol=Role.MEDICO,
        email=f"med-{uuid.uuid4()}@test.local",
    )
    db.add(m)
    db.flush()
    return m


@pytest.fixture
def admin(db):
    """Un admin de prueba (hace de 'creado_por' de las citas)."""
    a = User(
        nombre_completo="Admin Test",
        rol=Role.ADMIN,
        email=f"adm-{uuid.uuid4()}@test.local",
    )
    db.add(a)
    db.flush()
    return a


@pytest.fixture
def recepcion(db):
    """Un usuario de recepción de prueba (para los guardas por rol)."""
    r = User(
        nombre_completo="Recep Test",
        rol=Role.RECEPCION,
        email=f"rec-{uuid.uuid4()}@test.local",
    )
    db.add(r)
    db.flush()
    return r


@pytest.fixture
def service(db):
    """Un servicio de prueba del catálogo (nombre único)."""
    s = Service(
        nombre=f"Servicio {uuid.uuid4()}",
        categoria=ServiceCategory.CONSULTA,
    )
    db.add(s)
    db.flush()
    return s
