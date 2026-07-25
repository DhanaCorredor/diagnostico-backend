"""Lógica de negocio de pacientes: upsert al agendar + listar/ver/editar/dar de baja."""

import uuid

from sqlalchemy.orm import Session

from app.enums import Role
from app.models import User
from app.services.comun import valor_en_uso


class PacientesAmbiguos(Exception):
    """Varios pacientes coinciden; recepción debe elegir. Lleva la lista de candidatos."""

    def __init__(self, candidatos):
        self.candidatos = candidatos
        super().__init__(f"{len(candidatos)} pacientes coinciden; recepción debe elegir")


def buscar_o_crear_paciente(db: Session, nombre_completo: str, edad: int) -> User:
    """Busca un paciente por nombre_completo + edad y lo devuelve; si no existe, lo crea.

    Lanza PacientesAmbiguos si coinciden varios (recepción debe elegir). Flush, no commit.
    """
    coincidencias = (
        db.query(User)
        .filter(User.rol == Role.PACIENTE)
        .filter(User.activo.is_(True))
        .filter(User.nombre_completo == nombre_completo)
        .filter(User.edad == edad)
        .all()
    )
    if len(coincidencias) == 1:
        return coincidencias[0]
    if len(coincidencias) > 1:
        raise PacientesAmbiguos(coincidencias)

    paciente = User(nombre_completo=nombre_completo, edad=edad, rol=Role.PACIENTE)
    db.add(paciente)
    db.flush()
    return paciente


class PacienteNoEncontrado(Exception):
    """No existe un paciente con ese id."""


class CedulaDuplicada(Exception):
    """La cédula indicada ya pertenece a otra persona."""


def _cedula_en_uso(db: Session, cedula: str, excluir_id: uuid.UUID | None = None) -> bool:
    """True si la cédula ya pertenece a otra persona (excluyendo, si se indica, un id)."""
    return valor_en_uso(db, User, User.cedula, cedula, excluir_id)


def listar_pacientes(db: Session) -> list[User]:
    """Devuelve los pacientes activos, ordenados por nombre."""
    return (
        db.query(User)
        .filter(User.rol == Role.PACIENTE)
        .filter(User.activo.is_(True))
        .order_by(User.nombre_completo)
        .all()
    )


def obtener_paciente(db: Session, paciente_id: uuid.UUID) -> User:
    """Devuelve un paciente por id, o lanza PacienteNoEncontrado."""
    paciente = db.get(User, paciente_id)
    if paciente is None or paciente.rol != Role.PACIENTE:
        raise PacienteNoEncontrado()
    return paciente


def crear_paciente(db: Session, datos: dict) -> User:
    """Da de alta un paciente manualmente, sin deduplicar (cédula única si se indica). Flush, no commit."""
    cedula = datos.get("cedula")
    if cedula is not None and _cedula_en_uso(db, cedula):
        raise CedulaDuplicada()

    paciente = User(rol=Role.PACIENTE, **datos)
    db.add(paciente)
    db.flush()
    return paciente


def actualizar_paciente(db: Session, paciente_id: uuid.UUID, cambios: dict) -> User:
    """Actualiza solo los campos presentes en `cambios` (cédula única si se cambia). Flush, no commit."""
    paciente = obtener_paciente(db, paciente_id)

    nueva_cedula = cambios.get("cedula")
    if nueva_cedula is not None and _cedula_en_uso(db, nueva_cedula, excluir_id=paciente_id):
        raise CedulaDuplicada()

    for campo, valor in cambios.items():
        setattr(paciente, campo, valor)
    db.flush()
    return paciente


def desactivar_paciente(db: Session, paciente_id: uuid.UUID) -> User:
    """Da de baja (lógica) a un paciente: `activo=False`. Hace flush (no commit)."""
    paciente = obtener_paciente(db, paciente_id)
    paciente.activo = False
    db.flush()
    return paciente
