"""Lógica de negocio de pacientes: upsert al agendar.

Al crear una cita no se elige el paciente de una lista cerrada: recepción teclea
sus datos y el sistema decide si ya existe o hay que crearlo. Eso evita duplicados.
"""

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
