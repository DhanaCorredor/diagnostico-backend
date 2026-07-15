"""Punto de entrada del backend: crea la aplicación FastAPI y monta los routers."""

from fastapi import FastAPI

from app.routers import auth, citas, usuarios

# 'app' es la aplicación. El servidor (uvicorn) la busca por este nombre.
app = FastAPI(title="Diagnóstico API")

# Monta los routers (agrupan los endpoints).
app.include_router(auth.router)      # POST /auth/login, GET /auth/me
app.include_router(usuarios.router)  # GET /usuarios (solo ADMIN)
app.include_router(citas.router)     # POST /citas (recepción/admin)


@app.get("/health")
def health():
    """Endpoint de salud: sirve para comprobar que el servidor responde."""
    return {"status": "ok"}
