"""Conexión a la base de datos con SQLAlchemy."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()  # lee las variables del archivo .env y las deja disponibles

# La cadena de conexión (dónde está la BD y con qué credenciales). Viene del .env.
DATABASE_URL = os.getenv("DATABASE_URL")

# 'engine' es la conexión real a PostgreSQL.
engine = create_engine(DATABASE_URL)

# 'SessionLocal' fabrica sesiones: cada sesión es una "conversación" con la BD.
SessionLocal = sessionmaker(bind=engine, autoflush=False)

# 'Base' es la clase de la que heredarán todos los modelos (las tablas).
Base = declarative_base()
