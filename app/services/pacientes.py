"""Lógica de negocio de pacientes: upsert al agendar + listar/ver/editar (CRUD).

Al crear una cita, recepción teclea los datos y el sistema decide si el paciente
ya existe o hay que crearlo (evita duplicados). Además, la gestión de pacientes
permite listarlos, ver la ficha y editarla.
"""

import uuid

from sqlalchemy.orm import Session

from app.models import Rol, Usuario
from app.services.comun import valor_en_uso


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


def _cedula_en_uso(db: Session, cedula: str, excluir_id: uuid.UUID | None = None) -> bool:
    """True si la cédula ya pertenece a otra persona (excluyendo, si se indica, un id)."""
    return valor_en_uso(db, Usuario, Usuario.cedula, cedula, excluir_id)


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


def crear_paciente(db: Session, datos: dict) -> Usuario:
    """Da de alta un paciente de forma manual (sin agendar). Hace flush (no commit).

    La cédula, si se indica, debe ser única. No se deduplica por nombre+edad: es un
    alta explícita de recepción (para reutilizar uno existente está el upsert al agendar).
    """
    cedula = datos.get("cedula")
    if cedula is not None and _cedula_en_uso(db, cedula):  # única si viene
        raise CedulaDuplicada()

    paciente = Usuario(rol=Rol.PACIENTE, **datos)
    db.add(paciente)
    db.flush()  # asigna el id; el commit lo hace el endpoint
    return paciente


def actualizar_paciente(db: Session, paciente_id: uuid.UUID, cambios: dict) -> Usuario:
    """Actualiza SOLO los campos presentes en `cambios`. Hace flush (no commit).

    `cambios` viene del schema con `exclude_unset`, así que un campo **omitido** no
    se toca (no se borra). La cédula, si se cambia, debe ser única.
    """
    paciente = obtener_paciente(db, paciente_id)

    nueva_cedula = cambios.get("cedula")
    if nueva_cedula is not None and _cedula_en_uso(db, nueva_cedula, excluir_id=paciente_id):
        raise CedulaDuplicada()

    for campo, valor in cambios.items():
        setattr(paciente, campo, valor)
    db.flush()
    return paciente
