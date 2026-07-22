"""Punto de entrada del backend: crea la aplicación FastAPI y monta los routers."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, catalogo, citas, disponibilidad, pacientes, usuarios

load_dotenv()

# 'app' es la aplicación. El servidor (uvicorn) la busca por este nombre.
app = FastAPI(title="Diagnóstico API")

# CORS: el navegador solo deja al frontend (otro origen) llamar a esta API si el
# servidor lo autoriza. El origen sale del .env para poder cambiarlo en producción.
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta los routers (agrupan los endpoints).
app.include_router(auth.router)      # /auth: login (JWT) y me (autenticado)
app.include_router(usuarios.router)  # /usuarios: CRUD de personal/médicos (solo ADMIN)
app.include_router(citas.router)     # /citas: agendar, listar, editar/mover, cancelar, asistencia
app.include_router(catalogo.router)  # /servicios · /medicos · /especialidades: lectura (auth) + gestión (ADMIN)
app.include_router(disponibilidad.router)  # /disponibilidad: ver (auth) y definir franjas (ADMIN)
app.include_router(pacientes.router)  # /pacientes: CRUD e historial de citas (ADMIN/RECEPCIÓN)


@app.get("/health")
def health():
    """Endpoint de salud: sirve para comprobar que el servidor responde."""
    return {"status": "ok"}
