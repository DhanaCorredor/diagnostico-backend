"""Idempotent seed of base data: catalogs, staff and medical team. Run with `python -m app.seed`."""

import os
from datetime import time

from app.auth import hash_password
from app.db import SessionLocal
from app.enums import Role, ServiceCategory
from app.models import Availability, Service, Specialty, User

STAFF = [
    ("Administrador", "ADMIN", "admin@diagnostico.com", None),
    ("Recepción Demo", "RECEPCION", "recepcion@diagnostico.com", None),
    ("Dra. Ana Médico", "MEDICO", "medico@diagnostico.com", "MAT-0001"),
]

SPECIALTIES = [
    "Cardiología",
    "Medicina Interna",
    "Cirugía General",
    "Ginecología",
    "Gastroenterología",
    "Otorrinolaringología",
    "Traumatología",
    "Dermatología",
    "Venereología",
    "Neumonología",
    "Psicología",
    "Ecografía",
]

SERVICES = [
    ("Consulta cardiología", ServiceCategory.CONSULTA, ["Cardiología"]),
    ("Consulta medicina interna", ServiceCategory.CONSULTA, ["Medicina Interna"]),
    ("Consulta cirugía general", ServiceCategory.CONSULTA, ["Cirugía General"]),
    ("Consulta ginecología", ServiceCategory.CONSULTA, ["Ginecología"]),
    ("Consulta gastroenterología", ServiceCategory.CONSULTA, ["Gastroenterología"]),
    ("Consulta otorrinolaringología", ServiceCategory.CONSULTA, ["Otorrinolaringología"]),
    ("Consulta traumatología", ServiceCategory.CONSULTA, ["Traumatología"]),
    ("Consulta dermatología", ServiceCategory.CONSULTA, ["Dermatología"]),
    ("Consulta venereología", ServiceCategory.CONSULTA, ["Venereología"]),
    ("Consulta neumonología", ServiceCategory.CONSULTA, ["Neumonología"]),
    ("Consulta psicología", ServiceCategory.CONSULTA, ["Psicología"]),
    ("Ecografía abdominal", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía pélvica", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía renal", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía testicular", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía de partes blandas", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía mamaria", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía prostática", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía tiroidea", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía transvaginal", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Ecografía músculo-esquelética", ServiceCategory.ECOGRAFIA, ["Ecografía"]),
    ("Doppler carotídeo", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler hepático", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler renal", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler testicular", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler de partes blandas", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler mamario", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler prostático", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler tiroideo", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler pélvico", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler transvaginal", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler arterial y venoso (un miembro)", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Doppler arterial y venoso (ambos miembros)", ServiceCategory.DOPPLER, ["Ecografía"]),
    ("Ecocardiograma", ServiceCategory.ESTUDIO_CARDIACO, ["Cardiología"]),
    ("Electrocardiograma informado", ServiceCategory.ESTUDIO_CARDIACO, ["Cardiología"]),
    ("Electrocardiograma básico", ServiceCategory.ESTUDIO_CARDIACO, ["Cardiología"]),
    ("Holter de ritmo", ServiceCategory.ESTUDIO_CARDIACO, ["Cardiología"]),
    ("MAPA", ServiceCategory.ESTUDIO_CARDIACO, ["Cardiología"]),
    ("Espirometría", ServiceCategory.OTRO, ["Neumonología"]),
    ("Endoscopia nasal", ServiceCategory.OTRO, ["Otorrinolaringología"]),
    ("Plan Mujer (chequeo ginecológico completo)", ServiceCategory.PROMOCION, ["Ginecología"]),
    ("Cardiología (Holter + MAPA)", ServiceCategory.PROMOCION, ["Cardiología"]),
    ("2 ecografías convencionales", ServiceCategory.PROMOCION, ["Ecografía"]),
    ("Eco Doppler completo", ServiceCategory.PROMOCION, ["Ecografía"]),
    ("Neumonología + espirometría", ServiceCategory.PROMOCION, ["Neumonología"]),
]

MON, TUE, WED, THU, FRI, SAT = 1, 2, 3, 4, 5, 6
WORKDAYS = (MON, TUE, WED, THU, FRI, SAT)
OPEN_TIME = time(7, 30)
CLOSE_TIME = time(17, 30)
MORNING = (time(8, 0), time(13, 0))
AFTERNOON = (time(14, 0), CLOSE_TIME)

DOCTORS = [
    ("Dra. Fabiola González", ["Cardiología"],
     [(MON, *MORNING), (TUE, *MORNING), (WED, *AFTERNOON), (THU, *AFTERNOON)]),
    ("Divian Herrera", ["Cardiología"],
     [(TUE, *AFTERNOON), (THU, *MORNING), (FRI, *AFTERNOON)]),
    ("Dr. Richard Rodríguez", ["Cardiología"],
     [(WED, time(8, 0), CLOSE_TIME)]),
    ("Dra. Mariana Contreras", ["Cardiología"],
     [(MON, *AFTERNOON), (FRI, *MORNING), (SAT, *MORNING)]),
    ("Dr. Luis Peralta", ["Cardiología"],
     [(SAT, time(12, 0), CLOSE_TIME)]),
    ("Dra. Elsa Blanco", ["Otorrinolaringología"], []),
    ("Dra. Andrea Blanco", ["Dermatología", "Venereología"], []),
    ("Dra. Milaurys Fernández", ["Cirugía General"], []),
    ("Lic. Nathaly Rojas", ["Psicología"], []),
    ("Dra. Katherinne Castro", ["Traumatología"], []),
    ("Dra. Cristina Jiménez", ["Traumatología"], []),
    ("Dra. Neirys Magdaleno", ["Gastroenterología", "Medicina Interna"],
     [(FRI, time(13, 0), CLOSE_TIME)]),
    ("Dr. José Reyes", ["Gastroenterología"],
     [(TUE, time(8, 0), CLOSE_TIME)]),
    ("Dra. Jessika Colmenarez", ["Ginecología"],
     [(THU, time(8, 0), CLOSE_TIME)]),
    ("Dra. Nancy Borgas", ["Neumonología"],
     [(WED, time(13, 0), CLOSE_TIME)]),
    ("Dra. Nena Alvarado", ["Medicina Interna"],
     [(SAT, time(8, 0), CLOSE_TIME)]),
    ("Dra. Tania Hernández", ["Ecografía"],
     [(MON, time(13, 0), CLOSE_TIME), (TUE, time(13, 0), CLOSE_TIME),
      (WED, time(13, 0), CLOSE_TIME), (THU, time(7, 30), CLOSE_TIME)]),
    ("Dr. Michell Caballero", ["Ecografía"],
     [(MON, time(7, 30), CLOSE_TIME), (TUE, time(7, 30), CLOSE_TIME),
      (WED, time(7, 30), CLOSE_TIME), (FRI, time(7, 30), CLOSE_TIME),
      (SAT, time(7, 30), CLOSE_TIME)]),
]

PATIENTS = [
    ("María Fernández", 34, "V-13245678", "0412-1112233"),
    ("José Rodríguez", 51, "V-16234567", "0414-2223344"),
    ("Ana Gómez", 8, None, "0416-3334455"),
    ("Carlos Materán", 67, "V-14567891", "0424-4445566"),
    ("Luisa Pérez", 29, "V-18765432", "0426-6667788"),
]


def seed_specialties(db):
    """Insert the specialties that do not exist yet. Returns how many it added."""
    existing = {e.nombre for e in db.query(Specialty.nombre).all()}
    new_ones = [Specialty(nombre=n) for n in SPECIALTIES if n not in existing]
    db.add_all(new_ones)
    return len(new_ones)


def seed_services(db):
    """Insert the missing services and make sure they are linked (N:M) to their specialty.

    Idempotent: if a service already exists but has no specialties, they are linked (so the
    filter by doctor works without resetting the database). Returns how many services it created.
    """
    existing = {s.nombre: s for s in db.query(Service).all()}
    catalog = {e.nombre: e for e in db.query(Specialty).all()}
    created = 0
    for nombre, categoria, especialidades in SERVICES:
        service = existing.get(nombre)
        if service is None:
            service = Service(nombre=nombre, categoria=categoria)
            db.add(service)
            created += 1
        if not service.especialidades:
            service.especialidades = [catalog[e] for e in especialidades]
    return created


def seed_doctors(db):
    """Create the missing doctors (MEDICO role, no login), with their specialties (N:M) and slots. Returns how many it created."""
    existing = {
        u.nombre_completo
        for u in db.query(User.nombre_completo).filter(User.rol == Role.MEDICO).all()
    }
    catalog = {e.nombre: e for e in db.query(Specialty).all()}
    created = 0
    for nombre, especialidades, slots in DOCTORS:
        if nombre in existing:
            continue
        doctor = User(nombre_completo=nombre, rol=Role.MEDICO)
        doctor.especialidades = [catalog[e] for e in especialidades]
        db.add(doctor)
        db.flush()
        for day, start, end in slots:
            db.add(
                Availability(
                    usuario_id=doctor.id,
                    dia_semana=day,
                    hora_inicio=start,
                    hora_fin=end,
                )
            )
        created += 1
    return created


def seed_patients(db):
    """Create the missing fictional demo patients (PACIENTE role); never real data. Returns how many it created."""
    existing = {
        u.nombre_completo
        for u in db.query(User.nombre_completo).filter(User.rol == Role.PACIENTE).all()
    }
    created = 0
    for nombre, edad, cedula, telefono in PATIENTS:
        if nombre in existing:
            continue
        db.add(
            User(
                nombre_completo=nombre,
                rol=Role.PACIENTE,
                edad=edad,
                cedula=cedula,
                telefono=telefono,
            )
        )
        created += 1
    return created


def seed_staff(db):
    """Create the missing internal staff with login (admin, reception, doctor), using ADMIN_PASSWORD from .env. Returns how many it created."""
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        print("  (warning) ADMIN_PASSWORD is not in .env: skipping the staff.")
        return 0
    created = 0
    for nombre, rol, email, matricula in STAFF:
        if db.query(User).filter_by(email=email).first():
            continue
        db.add(
            User(
                nombre_completo=nombre,
                rol=Role(rol),
                email=email,
                matricula=matricula,
                password_hash=hash_password(password),
            )
        )
        created += 1
    return created


def seed_availability(db):
    """Give every doctor without slots the center's working hours (Mon-Sat 07:30-17:30); doctors that already have slots are left alone. Returns how many it created."""
    created = 0
    for doctor in db.query(User).filter(User.rol == Role.MEDICO).all():
        already_has_slots = (
            db.query(Availability)
            .filter(Availability.usuario_id == doctor.id)
            .first()
        )
        if already_has_slots:
            continue
        for day in WORKDAYS:
            db.add(
                Availability(
                    usuario_id=doctor.id,
                    dia_semana=day,
                    hora_inicio=OPEN_TIME,
                    hora_fin=CLOSE_TIME,
                )
            )
            created += 1
    return created


def main():
    db = SessionLocal()
    try:
        n_esp = seed_specialties(db)
        db.flush()
        n_serv = seed_services(db)
        n_med = seed_doctors(db)
        n_staff = seed_staff(db)
        db.flush()
        n_disp = seed_availability(db)
        n_pac = seed_patients(db)
        db.commit()
        print(
            f"Seed OK: +{n_esp} specialties, +{n_serv} services, "
            f"+{n_med} doctors, +{n_staff} staff, +{n_disp} availability slots, "
            f"+{n_pac} fictional patients."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
