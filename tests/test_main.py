"""Application configuration tests: the list of allowed origins (CORS)."""

from app.main import parse_origins


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
