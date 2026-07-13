"""Seed de datos base (catálogos): especialidades y servicios.

Idempotente: se puede ejecutar varias veces sin duplicar. Inserta solo lo que
falta (compara por `nombre`, que es único en ambas tablas).

Ejecutar con:  python -m app.seed
"""

import os

from app.auth import hashear_password
from app.db import SessionLocal
from app.models import Especialidad, Rol, Servicio, ServicioCategoria, Usuario

ADMIN_EMAIL = "admin@diagnostico.com"

# Personal de ejemplo para desarrollo: (nombre, rol, email, matrícula).
# Comparten la contraseña de desarrollo (ADMIN_PASSWORD); son solo para probar roles.
STAFF_DEMO = [
    ("Recepción Demo", "RECEPCION", "recepcion@diagnostico.com", None),
    ("Dra. Ana Médico", "MEDICO", "medico@diagnostico.com", "MAT-0001"),
]

# --- Catálogo de especialidades (~12, perfil real del centro) ---------------
ESPECIALIDADES = [
    "Cardiología",
    "Radiología / Ecografía",
    "Medicina Interna",
    "Ginecología",
    "Pediatría",
    "Dermatología",
    "Traumatología",
    "Otorrinolaringología",
    "Neurología",
    "Endocrinología",
    "Urología",
    "Gastroenterología",
]

# --- Catálogo de servicios: (nombre, categoría, duración en minutos) ---------
# La duración es la que marca el `ends_at` de cada cita.
SERVICIOS = [
    # Consultas
    ("Consulta cardiología", ServicioCategoria.CONSULTA, 30),
    ("Consulta medicina interna", ServicioCategoria.CONSULTA, 30),
    ("Consulta ginecología", ServicioCategoria.CONSULTA, 30),
    ("Consulta pediátrica", ServicioCategoria.CONSULTA, 20),
    ("Consulta dermatología", ServicioCategoria.CONSULTA, 20),
    ("Consulta traumatología", ServicioCategoria.CONSULTA, 20),
    # Ecografías
    ("Ecografía abdominal", ServicioCategoria.ECOGRAFIA, 20),
    ("Ecografía obstétrica", ServicioCategoria.ECOGRAFIA, 30),
    ("Ecografía mamaria", ServicioCategoria.ECOGRAFIA, 20),
    ("Ecografía tiroidea", ServicioCategoria.ECOGRAFIA, 15),
    ("Eco-doppler carotídeo", ServicioCategoria.ECOGRAFIA, 30),
    # Estudios cardíacos
    ("Ecocardiograma", ServicioCategoria.ESTUDIO_CARDIACO, 30),
    ("Electrocardiograma (ECG)", ServicioCategoria.ESTUDIO_CARDIACO, 15),
    ("Holter 24h (colocación)", ServicioCategoria.ESTUDIO_CARDIACO, 15),
    ("MAPA 24h (colocación)", ServicioCategoria.ESTUDIO_CARDIACO, 15),
    ("Prueba de esfuerzo", ServicioCategoria.ESTUDIO_CARDIACO, 45),
]


def sembrar_especialidades(db):
    """Inserta las especialidades que aún no existan. Devuelve cuántas añadió."""
    existentes = {e.nombre for e in db.query(Especialidad.nombre).all()}
    nuevas = [Especialidad(nombre=n) for n in ESPECIALIDADES if n not in existentes]
    db.add_all(nuevas)
    return len(nuevas)


def sembrar_servicios(db):
    """Inserta los servicios que aún no existan. Devuelve cuántos añadió."""
    existentes = {s.nombre for s in db.query(Servicio.nombre).all()}
    nuevos = [
        Servicio(nombre=nombre, categoria=categoria, duracion_min=duracion)
        for (nombre, categoria, duracion) in SERVICIOS
        if nombre not in existentes
    ]
    db.add_all(nuevos)
    return len(nuevos)


def sembrar_admin(db):
    """Crea el usuario ADMIN si no existe. Devuelve 1 si lo creó, 0 si no.

    La contraseña sale del .env (ADMIN_PASSWORD); nunca se escribe en el código.
    Si no está definida, se salta el admin con un aviso (no inventa contraseñas).
    """
    if db.query(Usuario).filter_by(email=ADMIN_EMAIL).first():
        return 0  # ya existe
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        print("  (aviso) ADMIN_PASSWORD no está en el .env: me salto el admin.")
        return 0
    db.add(
        Usuario(
            nombre_completo="Administrador",
            rol=Rol.ADMIN,
            email=ADMIN_EMAIL,
            password_hash=hashear_password(password),
        )
    )
    return 1


def sembrar_staff_demo(db):
    """Crea el personal de ejemplo (RECEPCION, MEDICO) que no exista. Devuelve cuántos creó.

    Usan la contraseña de desarrollo (ADMIN_PASSWORD). Si no está definida, se saltan.
    """
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        return 0
    creados = 0
    for nombre, rol, email, matricula in STAFF_DEMO:
        if db.query(Usuario).filter_by(email=email).first():
            continue
        db.add(
            Usuario(
                nombre_completo=nombre,
                rol=Rol(rol),
                email=email,
                matricula=matricula,
                password_hash=hashear_password(password),
            )
        )
        creados += 1
    return creados


def main():
    db = SessionLocal()
    try:
        n_esp = sembrar_especialidades(db)
        n_serv = sembrar_servicios(db)
        n_admin = sembrar_admin(db)
        n_staff = sembrar_staff_demo(db)
        db.commit()
        print(
            f"Seed OK: +{n_esp} especialidades, +{n_serv} servicios, "
            f"+{n_admin} admin, +{n_staff} staff."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
