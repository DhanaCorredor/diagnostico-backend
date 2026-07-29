"""Database connection tests: the engine must survive an idle database that suspends itself."""

from sqlalchemy import text

from app.db import engine


def test_engine_checks_connections_before_using_them():
    assert engine.pool._pre_ping is True


def test_engine_can_reach_the_database():
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar() == 1
