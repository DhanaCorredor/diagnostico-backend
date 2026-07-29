"""Backend entry point: creates the FastAPI application and mounts the routers."""

import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.controller import appointments, auth, availability, catalog, patients, users
from app.db import get_db

load_dotenv()

app = FastAPI(title="Diagnóstico API")

DEFAULT_ORIGIN = "http://localhost:5173"


def parse_origins(raw: str) -> list[str]:
    """Turn the comma-separated origins of the environment variable into a list."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


FRONTEND_ORIGINS = parse_origins(
    os.getenv("FRONTEND_ORIGINS") or os.getenv("FRONTEND_ORIGIN") or DEFAULT_ORIGIN
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(appointments.router)
app.include_router(catalog.router)
app.include_router(availability.router)
app.include_router(patients.router)


@app.exception_handler(IntegrityError)
def integrity_conflict(request: Request, exc: IntegrityError):
    """Translate a database constraint failure (unique or exclusion) into a 409 instead of a 500."""
    return JSONResponse(status_code=409, content={"detail": "Conflicto de integridad de datos"})


@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """Health endpoint: checks that the server responds and that the database answers.

    A managed database that suspends itself when idle can be unreachable while the server is
    perfectly fine, so the check queries it and answers 503 when it does not reply.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "unreachable"},
        )
    return {"status": "ok", "database": "ok"}
