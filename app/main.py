"""Punto de entrada del backend: crea la aplicación FastAPI y monta los routers."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, catalogo, citas, usuarios

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
app.include_router(auth.router)      # POST /auth/login, GET /auth/me
app.include_router(usuarios.router)  # GET /usuarios (solo ADMIN)
app.include_router(citas.router)     # POST /citas (recepción/admin)
app.include_router(catalogo.router)  # GET /servicios (autenticado)


@app.get("/health")
def health():
    """Endpoint de salud: sirve para comprobar que el servidor responde."""
    return {"status": "ok"}
