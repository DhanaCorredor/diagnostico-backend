"""Punto de entrada del backend: crea la aplicación FastAPI y monta los routers."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.controller import appointments, auth, availability, catalog, patients, users

load_dotenv()

app = FastAPI(title="Diagnóstico API")

DEFAULT_ORIGIN = "http://localhost:5173"


def parse_origins(raw: str) -> list[str]:
    """Convierte los orígenes separados por comas de la variable de entorno en una lista."""
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
    """Traduce un fallo de restricción única de la BD a un 409 (conflicto) en vez de un 500."""
    return JSONResponse(status_code=409, content={"detail": "Conflicto de integridad de datos"})


@app.get("/health")
def health():
    """Endpoint de salud: sirve para comprobar que el servidor responde."""
    return {"status": "ok"}
