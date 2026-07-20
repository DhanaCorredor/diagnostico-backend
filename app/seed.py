"""Seed de datos base (catálogos): especialidades y servicios.

Idempotente: se puede ejecutar varias veces sin duplicar. Inserta solo lo que
falta (compara por `nombre`, que es único en ambas tablas).

Ejecutar con:  python -m app.seed
"""

import os
from datetime import time

from app.auth import hashear_password
from app.db import SessionLocal
from app.models import Disponibilidad, Especialidad, Rol, Servicio, ServicioCategoria, Usuario

# Personal interno que hace login: (nombre, rol, email, matrícula).
# Todos comparten la contraseña del .env (ADMIN_PASSWORD); sin ella, se saltan.
STAFF = [
    ("Administrador", "ADMIN", "admin@diagnostico.com", None),
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

# --- Catálogo de servicios: (nombre, categoría) ------------------------------
# La duración ya no vive en el servicio: la elige recepción al agendar la cita.
SERVICIOS = [
    # Consultas
    ("Consulta cardiología", ServicioCategoria.CONSULTA),
    ("Consulta medicina interna", ServicioCategoria.CONSULTA),
    ("Consulta ginecología", ServicioCategoria.CONSULTA),
    ("Consulta pediátrica", ServicioCategoria.CONSULTA),
    ("Consulta dermatología", ServicioCategoria.CONSULTA),
    ("Consulta traumatología", ServicioCategoria.CONSULTA),
    # Ecografías
    ("Ecografía abdominal", ServicioCategoria.ECOGRAFIA),
    ("Ecografía obstétrica", ServicioCategoria.ECOGRAFIA),
    ("Ecografía mamaria", ServicioCategoria.ECOGRAFIA),
    ("Ecografía tiroidea", ServicioCategoria.ECOGRAFIA),
    ("Eco-doppler carotídeo", ServicioCategoria.ECOGRAFIA),
    # Estudios cardíacos
    ("Ecocardiograma", ServicioCategoria.ESTUDIO_CARDIACO),
    ("Electrocardiograma (ECG)", ServicioCategoria.ESTUDIO_CARDIACO),
    ("Holter 24h (colocación)", ServicioCategoria.ESTUDIO_CARDIACO),
    ("MAPA 24h (colocación)", ServicioCategoria.ESTUDIO_CARDIACO),
    ("Prueba de esfuerzo", ServicioCategoria.ESTUDIO_CARDIACO),
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
        Servicio(nombre=nombre, categoria=categoria)
        for (nombre, categoria) in SERVICIOS
        if nombre not in existentes
    ]
    db.add_all(nuevos)
    return len(nuevos)


def sembrar_staff(db):
    """Crea el personal interno (admin, recepción, médico) que no exista. Devuelve cuántos creó.

    Todos usan la contraseña del .env (ADMIN_PASSWORD); nunca se escribe en el código.
    Si no está definida, no crea a nadie (no inventa contraseñas).
    """
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        print("  (aviso) ADMIN_PASSWORD no está en el .env: me salto el personal.")
        return 0
    creados = 0
    for nombre, rol, email, matricula in STAFF:
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


# --- Disponibilidad por defecto de los médicos ------------------------------
# Cada médico sin franjas recibe una jornada estándar de lunes a viernes 08:00-14:00,
# para que la agenda tenga huecos utilizables sin depender de sobrecupos.
DIAS_LABORABLES = (1, 2, 3, 4, 5)  # lunes a viernes (0=domingo ... 6=sábado)


def sembrar_disponibilidad(db):
    """Da a cada médico SIN franjas una disponibilidad por defecto (L-V 08:00-14:00).

    Idempotente: si el médico ya tiene alguna franja, no la toca. Devuelve cuántas creó.
    """
    creadas = 0
    for medico in db.query(Usuario).filter(Usuario.rol == Rol.MEDICO).all():
        ya_tiene = (
            db.query(Disponibilidad)
            .filter(Disponibilidad.usuario_id == medico.id)
            .first()
        )
        if ya_tiene:
            continue
        for dia in DIAS_LABORABLES:
            db.add(
                Disponibilidad(
                    usuario_id=medico.id,
                    dia_semana=dia,
                    hora_inicio=time(8, 0),
                    hora_fin=time(14, 0),
                )
            )
            creadas += 1
    return creadas


def main():
    db = SessionLocal()
    try:
        n_esp = sembrar_especialidades(db)
        n_serv = sembrar_servicios(db)
        n_staff = sembrar_staff(db)
        db.flush()  # los médicos deben tener id antes de sembrar su disponibilidad
        n_disp = sembrar_disponibilidad(db)
        db.commit()
        print(
            f"Seed OK: +{n_esp} especialidades, +{n_serv} servicios, "
            f"+{n_staff} personal, +{n_disp} franjas de disponibilidad."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
