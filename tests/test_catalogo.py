"""Tests de las lecturas de catálogo (servicios, especialidades, médicos)."""

import uuid

from app.models import Servicio, ServicioCategoria
from app.services import catalogo as C


def test_listar_servicios_solo_activos_y_ordenados(db):
    # dos activos (con nombres desordenados) y uno inactivo
    activo_b = Servicio(nombre=f"B {uuid.uuid4()}", categoria=ServicioCategoria.CONSULTA)
    activo_a = Servicio(nombre=f"A {uuid.uuid4()}", categoria=ServicioCategoria.ECOGRAFIA)
    inactivo = Servicio(
        nombre=f"Z {uuid.uuid4()}", categoria=ServicioCategoria.OTRO, activo=False
    )
    db.add_all([activo_b, activo_a, inactivo])
    db.flush()

    nombres = [s.nombre for s in C.listar_servicios(db)]
    assert activo_a.nombre in nombres and activo_b.nombre in nombres
    assert inactivo.nombre not in nombres          # los inactivos no salen
    # ordenados por nombre: 'A...' aparece antes que 'B...'
    assert nombres.index(activo_a.nombre) < nombres.index(activo_b.nombre)
