"""Lógica de negocio de pacientes: upsert al agendar + listar/ver/editar (CRUD).

Al crear una cita, recepción teclea los datos y el sistema decide si el paciente
ya existe o hay que crearlo (evita duplicados). Además, la gestión de pacientes
permite listarlos, ver la ficha y editarla.
"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models import Rol, Usuario


class PacientesAmbiguos(Exception):
    """Hay varios pacientes que coinciden; recepción debe elegir uno.

    Lleva la lista de candidatos para que el endpoint la muestre.
    """

    def __init__(self, candidatos):
        self.candidatos = candidatos
        super().__init__(f"{len(candidatos)} pacientes coinciden; recepción debe elegir")


def buscar_o_crear_paciente(db: Session, nombre_completo: str, edad: int) -> Usuario:
    """Busca un paciente por nombre_completo + edad; si no existe, lo crea.

    - Uno solo coincide  -> lo devuelve (reutiliza).
    - Ninguno coincide   -> crea uno nuevo con rol PACIENTE y lo devuelve.
    - Varios coinciden   -> lanza PacientesAmbiguos (recepción debe elegir).

    Hace flush (no commit): el paciente nuevo obtiene su id, pero se guarda dentro
    de la transacción de quien llame (junto con la cita).
    """
    coincidencias = (
        db.query(Usuario)
        .filter(Usuario.rol == Rol.PACIENTE)
        .filter(Usuario.nombre_completo == nombre_completo)
        .filter(Usuario.edad == edad)
        .all()
    )
    if len(coincidencias) == 1:
        return coincidencias[0]
    if len(coincidencias) > 1:
        raise PacientesAmbiguos(coincidencias)

    paciente = Usuario(nombre_completo=nombre_completo, edad=edad, rol=Rol.PACIENTE)
    db.add(paciente)
    db.flush()  # asigna el id sin cerrar la transacción
    return paciente


# --- Gestión de pacientes (listar / ver / editar) ---------------------------


class PacienteNoEncontrado(Exception):
    """No existe un paciente con ese id."""


class CedulaDuplicada(Exception):
    """La cédula indicada ya pertenece a otra persona."""


def listar_pacientes(db: Session) -> list[Usuario]:
    """Devuelve todos los pacientes, ordenados por nombre."""
    return (
        db.query(Usuario)
        .filter(Usuario.rol == Rol.PACIENTE)
        .order_by(Usuario.nombre_completo)
        .all()
    )


def obtener_paciente(db: Session, paciente_id: uuid.UUID) -> Usuario:
    """Devuelve un paciente por id, o lanza PacienteNoEncontrado."""
    paciente = db.get(Usuario, paciente_id)
    if paciente is None or paciente.rol != Rol.PACIENTE:
        raise PacienteNoEncontrado()
    return paciente


def actualizar_paciente(
    db: Session,
    paciente_id: uuid.UUID,
    *,
    nombre_completo: str,
    edad: int,
    cedula: str | None,
    telefono: str | None,
    fecha_nacimiento: date | None,
) -> Usuario:
    """Edita un paciente. La cédula (si se indica) debe ser única. Hace flush (no commit)."""
    paciente = obtener_paciente(db, paciente_id)
    # cédula única: no puede coincidir con la de OTRA persona
    if cedula is not None:
        otro = (
            db.query(Usuario)
            .filter(Usuario.cedula == cedula)
            .filter(Usuario.id != paciente_id)
            .first()
        )
        if otro is not None:
            raise CedulaDuplicada()

    paciente.nombre_completo = nombre_completo
    paciente.edad = edad
    paciente.cedula = cedula
    paciente.telefono = telefono
    paciente.fecha_nacimiento = fecha_nacimiento
    db.flush()
    return paciente
