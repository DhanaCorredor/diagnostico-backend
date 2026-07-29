"""Database connection with SQLAlchemy.

`pool_pre_ping` checks that a pooled connection is still alive before handing it out. A
managed database that suspends itself when idle drops those connections, and without this
check the first request after the suspension fails with `SSL SYSCALL error: EOF detected`.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta DATABASE_URL en el .env (cadena de conexión a PostgreSQL).")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)

Base = declarative_base()


def get_db():
    """FastAPI dependency: opens a database session for the request and closes it at the end."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
