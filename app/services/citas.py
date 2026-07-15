"""Lógica de negocio de las citas: duración, disponibilidad y anti-solapamiento.

Estas funciones son el núcleo del proyecto. Viven separadas de los endpoints
para poder probarlas de forma aislada.
"""

from datetime import datetime, timedelta

from app.models import Servicio


def calcular_ends_at(starts_at: datetime, servicio: Servicio) -> datetime:
    """Calcula cuándo termina la cita: inicio + la duración que marca el servicio.

    La cita no guarda su propia duración; la hereda del servicio en este momento.
    Ej.: 10:00 + Consulta (45 min) -> 10:45.
    """
    return starts_at + timedelta(minutes=servicio.duracion_min)
