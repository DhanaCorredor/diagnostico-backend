"""Configuración común de los tests: sesión de BD aislada y datos de apoyo.

Cada test corre dentro de una transacción que se revierte al terminar (rollback),
así las pruebas no dejan rastro en la base de datos.
"""

import uuid

import pytest

from app.db import SessionLocal, engine
from app.models import Rol, Servicio, ServicioCategoria, Usuario


@pytest.fixture
def db():
    """Sesión envuelta en una transacción que se revierte al final del test."""
    connection = engine.connect()
    trans = connection.begin()
    session = SessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


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
def servicio(db):
    """Un servicio de prueba del catálogo (nombre único)."""
    s = Servicio(
        nombre=f"Servicio {uuid.uuid4()}",
        categoria=ServicioCategoria.CONSULTA,
    )
    db.add(s)
    db.flush()
    return s
