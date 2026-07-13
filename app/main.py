"""Punto de entrada del backend: crea la aplicación FastAPI y monta los routers."""

from fastapi import FastAPI

from app.routers import auth

# 'app' es la aplicación. El servidor (uvicorn) la busca por este nombre.
app = FastAPI(title="Diagnóstico API")

# Monta los endpoints de autenticación (POST /auth/login, GET /auth/me).
app.include_router(auth.router)


@app.get("/health")
def health():
    """Endpoint de salud: sirve para comprobar que el servidor responde."""
    return {"status": "ok"}
