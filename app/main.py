"""Punto de entrada del backend: crea la aplicación FastAPI."""

from fastapi import FastAPI

# 'app' es la aplicación. El servidor (uvicorn) la busca por este nombre.
app = FastAPI(title="Diagnóstico API")


@app.get("/health")
def health():
    """Endpoint de salud: sirve para comprobar que el servidor responde."""
    return {"status": "ok"}
