"""Punto de entrada del backend: crea la aplicación FastAPI y monta los routers."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.controller import auth, catalogo, citas, disponibilidad, pacientes, usuarios

load_dotenv()

app = FastAPI(title="Diagnóstico API")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(citas.router)
app.include_router(catalogo.router)
app.include_router(disponibilidad.router)
app.include_router(pacientes.router)


@app.exception_handler(IntegrityError)
def conflicto_de_integridad(request: Request, exc: IntegrityError):
    """Traduce un fallo de restricción única de la BD a un 409 (conflicto) en vez de un 500."""
    return JSONResponse(status_code=409, content={"detail": "Conflicto de integridad de datos"})


@app.get("/health")
def health():
    """Endpoint de salud: sirve para comprobar que el servidor responde."""
    return {"status": "ok"}
