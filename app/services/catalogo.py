"""Lecturas de catálogo: servicios, especialidades y médicos.

Son consultas de solo lectura que alimentan los desplegables del frontend
(elegir servicio, especialidad o médico al agendar). Viven en la capa de
servicio para poder probarlas sin levantar la API.
"""

from sqlalchemy.orm import Session

from app.models import Especialidad, Rol, Servicio, Usuario


def listar_servicios(db: Session) -> list[Servicio]:
    """Devuelve los servicios activos del catálogo, ordenados por nombre."""
    return (
        db.query(Servicio)
        .filter(Servicio.activo.is_(True))
        .order_by(Servicio.nombre)
        .all()
    )


def listar_medicos(db: Session) -> list[Usuario]:
    """Devuelve los médicos activos, ordenados por nombre, con sus especialidades."""
    return (
        db.query(Usuario)
        .filter(Usuario.rol == Rol.MEDICO)
        .filter(Usuario.activo.is_(True))
        .order_by(Usuario.nombre_completo)
        .all()
    )


def listar_especialidades(db: Session) -> list[Especialidad]:
    """Devuelve todas las especialidades del catálogo, ordenadas por nombre."""
    return db.query(Especialidad).order_by(Especialidad.nombre).all()
