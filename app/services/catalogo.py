"""Lecturas de catálogo: servicios, especialidades y médicos.

Son consultas de solo lectura que alimentan los desplegables del frontend
(elegir servicio, especialidad o médico al agendar). Viven en la capa de
servicio para poder probarlas sin levantar la API.
"""

from sqlalchemy.orm import Session

from app.models import Servicio


def listar_servicios(db: Session) -> list[Servicio]:
    """Devuelve los servicios activos del catálogo, ordenados por nombre."""
    return (
        db.query(Servicio)
        .filter(Servicio.activo.is_(True))
        .order_by(Servicio.nombre)
        .all()
    )
