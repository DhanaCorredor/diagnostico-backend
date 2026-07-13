"""Seed de datos base (catálogos): especialidades y servicios.

Idempotente: se puede ejecutar varias veces sin duplicar. Inserta solo lo que
falta (compara por `nombre`, que es único en ambas tablas).

Ejecutar con:  python -m app.seed
"""

from app.db import SessionLocal
from app.models import Especialidad, Servicio, ServicioCategoria

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


def main():
    db = SessionLocal()
    try:
        n_esp = sembrar_especialidades(db)
        n_serv = sembrar_servicios(db)
        db.commit()
        print(f"Seed OK: +{n_esp} especialidades, +{n_serv} servicios.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
