"""Tests de disponibilidad: listar franjas + crear con sus validaciones."""

from datetime import time

import pytest

from app.services import disponibilidad as D


def test_crear_y_listar_disponibilidad(db, medico):
    D.crear_disponibilidad(
        db, medico_id=medico.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(14, 0)
    )
    franjas = D.listar_disponibilidad(db, medico.id)
    assert len(franjas) == 1
    assert franjas[0].dia_semana == 1
    assert franjas[0].hora_inicio == time(8, 0)


def test_crear_disponibilidad_medico_invalido(db, admin):
    with pytest.raises(D.MedicoNoEncontrado):
        D.crear_disponibilidad(
            db, medico_id=admin.id, dia_semana=1, hora_inicio=time(8, 0), hora_fin=time(14, 0)
        )


def test_crear_disponibilidad_franja_invalida(db, medico):
    with pytest.raises(D.FranjaInvalida):
        D.crear_disponibilidad(
            db, medico_id=medico.id, dia_semana=1, hora_inicio=time(14, 0), hora_fin=time(8, 0)
        )
