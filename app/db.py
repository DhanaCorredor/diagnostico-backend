"""Conexión a la base de datos con SQLAlchemy."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()  # lee las variables del archivo .env y las deja disponibles

# La cadena de conexión (dónde está la BD y con qué credenciales). Viene del .env.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Sin BD no hay nada que hacer: fallar aquí con un mensaje claro es mejor que
    # un error confuso más adelante al intentar conectar.
    raise RuntimeError("Falta DATABASE_URL en el .env (cadena de conexión a PostgreSQL).")

# 'engine' es la conexión real a PostgreSQL.
engine = create_engine(DATABASE_URL)

# 'SessionLocal' fabrica sesiones: cada sesión es una "conversación" con la BD.
SessionLocal = sessionmaker(bind=engine, autoflush=False)

# 'Base' es la clase de la que heredarán todos los modelos (las tablas).
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: abre una sesión para la petición y la cierra al final.

    El 'yield' entrega la sesión al endpoint; el 'finally' garantiza que se cierre
    aunque haya un error. Cada petición usa su propia sesión.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
