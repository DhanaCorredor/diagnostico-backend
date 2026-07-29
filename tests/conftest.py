"""Shared test setup: an isolated database session and supporting data.

Every test runs inside a transaction that is rolled back at the end, so the
tests leave no trace in the database.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth import create_token
from app.db import SessionLocal, engine, get_db
from app.enums import Role, ServiceCategory
from app.main import app
from app.models import Service, User


@pytest.fixture
def db():
    """Session wrapped in a transaction that is rolled back at the end of the test.

    `join_transaction_mode="create_savepoint"`: the `commit()` calls made by the
    endpoints (in the integration tests) are confined to a SAVEPOINT, so the final
    rollback undoes them anyway and nothing is left in the database.
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
    """TestClient with the test database injected: the app uses the SAME session as the test.

    Overrides the `get_db` dependency so the endpoints share the test's
    transaction (which is rolled back at the end).
    """
    def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def token_for():
    """Return a function that builds the Authorization header of a user."""
    def _header(user):
        return {"Authorization": f"Bearer {create_token(user.id)}"}

    return _header


@pytest.fixture
def doctor(db):
    """A test doctor (unique email so it does not clash with others)."""
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
    """A test admin (acts as the 'creado_por' of the appointments)."""
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
    """A test reception user (for the role guards)."""
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
    """A test catalog service (unique name)."""
    s = Service(
        nombre=f"Servicio {uuid.uuid4()}",
        categoria=ServiceCategory.CONSULTA,
    )
    db.add(s)
    db.flush()
    return s
