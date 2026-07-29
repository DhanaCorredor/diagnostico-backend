"""Application tests: allowed origins (CORS) and the health endpoint."""

from sqlalchemy.exc import SQLAlchemyError

from app.db import get_db
from app.main import app, parse_origins


def test_parse_origins_single():
    assert parse_origins("http://localhost:5173") == ["http://localhost:5173"]


def test_parse_origins_multiple():
    raw = "http://localhost:5173,https://front.onrender.com"
    assert parse_origins(raw) == ["http://localhost:5173", "https://front.onrender.com"]


def test_parse_origins_ignores_spaces_and_empties():
    raw = " http://localhost:5173 , , https://front.onrender.com ,"
    assert parse_origins(raw) == ["http://localhost:5173", "https://front.onrender.com"]


def test_allowed_origin_gets_cors_header(client):
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_unknown_origin_gets_no_cors_header(client):
    r = client.get("/health", headers={"Origin": "https://sitio-no-autorizado.com"})
    assert r.status_code == 200
    assert "access-control-allow-origin" not in r.headers


def test_health_reports_a_reachable_database(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_health_reports_an_unreachable_database(client):
    class UnreachableSession:
        def execute(self, *args, **kwargs):
            raise SQLAlchemyError("the database does not answer")

    def _unreachable_db():
        yield UnreachableSession()

    app.dependency_overrides[get_db] = _unreachable_db

    r = client.get("/health")
    assert r.status_code == 503
    assert r.json() == {"status": "error", "database": "unreachable"}
