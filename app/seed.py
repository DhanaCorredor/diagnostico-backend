"""Seed idempotente de datos base: catálogos, personal y cuadro médico. Ejecutar con `python -m app.seed`."""

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
MORNING = (time(8, 0), time(13, 0))
AFTERNOON = (time(14, 0), time(17, 30))
CLOSE = time(17, 30)

DOCTORS = [
    ("Dra. Fabiola González", ["Cardiología"],
     [(MON, *MORNING), (TUE, *MORNING), (WED, *AFTERNOON), (THU, *AFTERNOON)]),
    ("Divian Herrera", ["Cardiología"],
     [(TUE, *AFTERNOON), (THU, *MORNING), (FRI, *AFTERNOON)]),
    ("Dr. Richard Rodríguez", ["Cardiología"],
     [(WED, time(8, 0), CLOSE)]),
    ("Dra. Mariana Contreras", ["Cardiología"],
     [(MON, *AFTERNOON), (FRI, *MORNING), (SAT, *MORNING)]),
    ("Dr. Luis Peralta", ["Cardiología"],
     [(SAT, time(12, 0), CLOSE)]),
    ("Dra. Elsa Blanco", ["Otorrinolaringología"], []),
    ("Dra. Andrea Blanco", ["Dermatología", "Venereología"], []),
    ("Dra. Milaurys Fernández", ["Cirugía General"], []),
    ("Lic. Nathaly Rojas", ["Psicología"], []),
    ("Dra. Katherinne Castro", ["Traumatología"], []),
    ("Dra. Cristina Jiménez", ["Traumatología"], []),
    ("Dra. Neirys Magdaleno", ["Gastroenterología", "Medicina Interna"],
     [(FRI, time(13, 0), CLOSE)]),
    ("Dr. José Reyes", ["Gastroenterología"],
     [(TUE, time(8, 0), CLOSE)]),
    ("Dra. Jessika Colmenarez", ["Ginecología"],
     [(THU, time(8, 0), CLOSE)]),
    ("Dra. Nancy Borgas", ["Neumonología"],
     [(WED, time(13, 0), CLOSE)]),
    ("Dra. Nena Alvarado", ["Medicina Interna"],
     [(SAT, time(8, 0), CLOSE)]),
    ("Dra. Tania Hernández", ["Ecografía"],
     [(MON, time(13, 0), CLOSE), (TUE, time(13, 0), CLOSE),
      (WED, time(13, 0), CLOSE), (THU, time(7, 30), CLOSE)]),
    ("Dr. Michell Caballero", ["Ecografía"],
     [(MON, time(7, 30), CLOSE), (TUE, time(7, 30), CLOSE),
      (WED, time(7, 30), CLOSE), (FRI, time(7, 30), CLOSE),
      (SAT, time(7, 30), CLOSE)]),
]

PATIENTS = [
    ("María Fernández", 34, "V-13245678", "0412-1112233"),
    ("José Rodríguez", 51, "V-16234567", "0414-2223344"),
    ("Ana Gómez", 8, None, "0416-3334455"),
    ("Carlos Materán", 67, "V-14567891", "0424-4445566"),
    ("Luisa Pérez", 29, "V-18765432", "0426-6667788"),
]


def seed_specialties(db):
    """Inserta las especialidades que aún no existan. Devuelve cuántas añadió."""
    existing = {e.nombre for e in db.query(Specialty.nombre).all()}
    new_ones = [Specialty(nombre=n) for n in SPECIALTIES if n not in existing]
    db.add_all(new_ones)
    return len(new_ones)


def seed_services(db):
    """Inserta los servicios que falten y asegura su vínculo (N:M) con la especialidad.

    Idempotente: si un servicio ya existe pero sin especialidades, se las enlaza (así el
    filtro por médico funciona sin resetear la base). Devuelve cuántos servicios creó.
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
    """Crea los médicos que falten (rol MEDICO, sin login), con sus especialidades (N:M) y franjas. Devuelve cuántos creó."""
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
        for dia, start, end in slots:
            db.add(
                Availability(
                    usuario_id=doctor.id,
                    dia_semana=dia,
                    hora_inicio=start,
                    hora_fin=end,
                )
            )
        created += 1
    return created


def seed_patients(db):
    """Crea los pacientes ficticios de demo (rol PACIENTE) que falten; nunca datos reales. Devuelve cuántos creó."""
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
    """Crea el personal interno con login (admin, recepción, médico) que falte, usando ADMIN_PASSWORD del .env. Devuelve cuántos creó."""
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        print("  (aviso) ADMIN_PASSWORD no está en el .env: me salto el personal.")
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


WORKDAYS = (1, 2, 3, 4, 5, 6)
OPEN_TIME = time(7, 30)
CLOSE_TIME = time(17, 30)


def seed_availability(db):
    """Da a cada médico sin franjas la jornada del centro (L-S 07:30-17:30); no toca a los que ya tienen. Devuelve cuántas creó."""
    created = 0
    for doctor in db.query(User).filter(User.rol == Role.MEDICO).all():
        ya_tiene = (
            db.query(Availability)
            .filter(Availability.usuario_id == doctor.id)
            .first()
        )
        if ya_tiene:
            continue
        for dia in WORKDAYS:
            db.add(
                Availability(
                    usuario_id=doctor.id,
                    dia_semana=dia,
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
            f"Seed OK: +{n_esp} especialidades, +{n_serv} servicios, "
            f"+{n_med} médicos, +{n_staff} personal, +{n_disp} franjas de disponibilidad, "
            f"+{n_pac} pacientes ficticios."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
