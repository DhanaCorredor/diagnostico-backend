"""Seed de datos base: catálogos (especialidades y servicios), personal y cuadro médico.

Idempotente: se puede ejecutar varias veces sin duplicar. Inserta solo lo que
falta (compara por `nombre`, que es único en catálogos; los médicos, por
`nombre_completo`).

Ejecutar con:  python -m app.seed
"""

import os
from datetime import time

from app.auth import hashear_password
from app.db import SessionLocal
from app.models import Disponibilidad, Especialidad, Rol, Servicio, ServicioCategoria, Usuario

STAFF = [
    ("Administrador", "ADMIN", "admin@diagnostico.com", None),
    ("Recepción Demo", "RECEPCION", "recepcion@diagnostico.com", None),
    ("Dra. Ana Médico", "MEDICO", "medico@diagnostico.com", "MAT-0001"),
]

ESPECIALIDADES = [
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

SERVICIOS = [
    ("Consulta cardiología", ServicioCategoria.CONSULTA),
    ("Consulta medicina interna", ServicioCategoria.CONSULTA),
    ("Consulta cirugía general", ServicioCategoria.CONSULTA),
    ("Consulta ginecología", ServicioCategoria.CONSULTA),
    ("Consulta gastroenterología", ServicioCategoria.CONSULTA),
    ("Consulta otorrinolaringología", ServicioCategoria.CONSULTA),
    ("Consulta traumatología", ServicioCategoria.CONSULTA),
    ("Consulta dermatología", ServicioCategoria.CONSULTA),
    ("Consulta venereología", ServicioCategoria.CONSULTA),
    ("Consulta neumonología", ServicioCategoria.CONSULTA),
    ("Consulta psicología", ServicioCategoria.CONSULTA),
    ("Ecografía abdominal", ServicioCategoria.ECOGRAFIA),
    ("Ecografía pélvica", ServicioCategoria.ECOGRAFIA),
    ("Ecografía renal", ServicioCategoria.ECOGRAFIA),
    ("Ecografía testicular", ServicioCategoria.ECOGRAFIA),
    ("Ecografía de partes blandas", ServicioCategoria.ECOGRAFIA),
    ("Ecografía mamaria", ServicioCategoria.ECOGRAFIA),
    ("Ecografía prostática", ServicioCategoria.ECOGRAFIA),
    ("Ecografía tiroidea", ServicioCategoria.ECOGRAFIA),
    ("Ecografía transvaginal", ServicioCategoria.ECOGRAFIA),
    ("Ecografía músculo-esquelética", ServicioCategoria.ECOGRAFIA),
    ("Doppler carotídeo", ServicioCategoria.DOPPLER),
    ("Doppler hepático", ServicioCategoria.DOPPLER),
    ("Doppler renal", ServicioCategoria.DOPPLER),
    ("Doppler testicular", ServicioCategoria.DOPPLER),
    ("Doppler de partes blandas", ServicioCategoria.DOPPLER),
    ("Doppler mamario", ServicioCategoria.DOPPLER),
    ("Doppler prostático", ServicioCategoria.DOPPLER),
    ("Doppler tiroideo", ServicioCategoria.DOPPLER),
    ("Doppler pélvico", ServicioCategoria.DOPPLER),
    ("Doppler transvaginal", ServicioCategoria.DOPPLER),
    ("Doppler arterial y venoso (un miembro)", ServicioCategoria.DOPPLER),
    ("Doppler arterial y venoso (ambos miembros)", ServicioCategoria.DOPPLER),
    ("Ecocardiograma", ServicioCategoria.ESTUDIO_CARDIACO),
    ("Electrocardiograma informado", ServicioCategoria.ESTUDIO_CARDIACO),
    ("Electrocardiograma básico", ServicioCategoria.ESTUDIO_CARDIACO),
    ("Holter de ritmo", ServicioCategoria.ESTUDIO_CARDIACO),
    ("MAPA", ServicioCategoria.ESTUDIO_CARDIACO),
    ("Espirometría", ServicioCategoria.OTRO),
    ("Endoscopia nasal", ServicioCategoria.OTRO),
]

LUN, MAR, MIE, JUE, VIE, SAB = 1, 2, 3, 4, 5, 6
MANANA = (time(8, 0), time(13, 0))
TARDE = (time(14, 0), time(17, 30))
CIERRE = time(17, 30)

MEDICOS = [
    ("Dra. Fabiola González", ["Cardiología"],
     [(LUN, *MANANA), (MAR, *MANANA), (MIE, *TARDE), (JUE, *TARDE)]),
    ("Divian Herrera", ["Cardiología"],
     [(MAR, *TARDE), (JUE, *MANANA), (VIE, *TARDE)]),
    ("Dr. Richard Rodríguez", ["Cardiología"],
     [(MIE, *MANANA), (VIE, *TARDE)]),
    ("Dra. Mariana Contreras", ["Cardiología"],
     [(LUN, *TARDE), (VIE, *MANANA), (SAB, *MANANA)]),
    ("Dr. Luis Peralta", ["Cardiología"],
     [(SAB, time(12, 0), CIERRE)]),
    ("Dra. Elsa Blanco", ["Otorrinolaringología"], []),
    ("Dra. Andrea Blanco", ["Dermatología"], []),
    ("Lic. Nathaly Rojas", ["Psicología"], []),
    ("Dra. Katherinne Castro", ["Traumatología"], []),
    ("Dra. Cristina Jiménez", ["Traumatología"], []),
    ("Dra. Neirys Magdaleno", ["Gastroenterología", "Medicina Interna"],
     [(VIE, time(13, 0), CIERRE)]),
    ("Dr. José Reyes", ["Gastroenterología"],
     [(MAR, time(8, 0), CIERRE)]),
    ("Dra. Jessika Colmenarez", ["Ginecología"],
     [(JUE, time(8, 0), CIERRE)]),
    ("Dra. Nancy Borgas", ["Neumonología"],
     [(MIE, time(13, 0), CIERRE)]),
    ("Dra. Nena Alvarado", ["Medicina Interna"],
     [(SAB, time(8, 0), CIERRE)]),
    ("Dra. Tania Hernández", ["Ecografía"],
     [(LUN, time(7, 30), CIERRE), (MIE, time(7, 30), CIERRE)]),
    ("Dr. Michell Caballero", ["Ecografía"],
     [(LUN, time(7, 30), CIERRE), (MIE, time(7, 30), CIERRE)]),
]

PACIENTES = [
    ("María Fernández", 34, "V-13245678", "0412-1112233"),
    ("José Rodríguez", 51, "V-16234567", "0414-2223344"),
    ("Ana Gómez", 8, None, "0416-3334455"),
    ("Carlos Materán", 67, "V-14567891", "0424-4445566"),
    ("Luisa Pérez", 29, "V-18765432", "0426-6667788"),
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


def sembrar_medicos(db):
    """Crea los médicos del cuadro médico (rol MEDICO, sin login) que no existan.

    - Sin email ni contraseña: no hacen login (recepción agenda por ellos).
    - Vincula sus especialidades (N:M); deben existir ya (se siembran antes).
    - Crea sus franjas del briefing; los que no traen ninguna reciben la jornada
      completa del centro en sembrar_disponibilidad().

    Idempotente: compara por `nombre_completo`. Devuelve cuántos creó.
    """
    existentes = {
        u.nombre_completo
        for u in db.query(Usuario.nombre_completo).filter(Usuario.rol == Rol.MEDICO).all()
    }
    catalogo = {e.nombre: e for e in db.query(Especialidad).all()}
    creados = 0
    for nombre, especialidades, franjas in MEDICOS:
        if nombre in existentes:
            continue
        medico = Usuario(nombre_completo=nombre, rol=Rol.MEDICO)
        medico.especialidades = [catalogo[e] for e in especialidades]
        db.add(medico)
        db.flush()
        for dia, inicio, fin in franjas:
            db.add(
                Disponibilidad(
                    usuario_id=medico.id,
                    dia_semana=dia,
                    hora_inicio=inicio,
                    hora_fin=fin,
                )
            )
        creados += 1
    return creados


def sembrar_pacientes(db):
    """Crea los pacientes FICTICIOS de demo (rol PACIENTE) que no existan.

    Datos inventados: nunca se usan pacientes reales del centro. Idempotente por
    `nombre_completo`. Devuelve cuántos creó.
    """
    existentes = {
        u.nombre_completo
        for u in db.query(Usuario.nombre_completo).filter(Usuario.rol == Rol.PACIENTE).all()
    }
    creados = 0
    for nombre, edad, cedula, telefono in PACIENTES:
        if nombre in existentes:
            continue
        db.add(
            Usuario(
                nombre_completo=nombre,
                rol=Rol.PACIENTE,
                edad=edad,
                cedula=cedula,
                telefono=telefono,
            )
        )
        creados += 1
    return creados


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


DIAS_LABORABLES = (1, 2, 3, 4, 5, 6)
HORA_APERTURA = time(7, 30)
HORA_CIERRE = time(17, 30)


def sembrar_disponibilidad(db):
    """Da a cada médico SIN franjas la jornada del centro (L-S 07:30-17:30).

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
                    hora_inicio=HORA_APERTURA,
                    hora_fin=HORA_CIERRE,
                )
            )
            creadas += 1
    return creadas


def main():
    db = SessionLocal()
    try:
        n_esp = sembrar_especialidades(db)
        n_serv = sembrar_servicios(db)
        db.flush()
        n_med = sembrar_medicos(db)
        n_staff = sembrar_staff(db)
        db.flush()
        n_disp = sembrar_disponibilidad(db)
        n_pac = sembrar_pacientes(db)
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
