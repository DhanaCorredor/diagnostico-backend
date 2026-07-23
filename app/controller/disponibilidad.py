"""Router de disponibilidad: ver las franjas de un médico y definirlas.

- GET: cualquier usuario autenticado (el calendario la lee para bloquear).
- POST: solo ADMIN (define los horarios de los médicos).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import requiere_rol, usuario_actual
from app.db import get_db
from app.enums import Rol
from app.models import Usuario
from app.schemas import DisponibilidadCreate, DisponibilidadOut
from app.services import disponibilidad as disp_service

router = APIRouter(prefix="/disponibilidad", tags=["disponibilidad"])


@router.get("", response_model=list[DisponibilidadOut])
async def listar_disponibilidad(
    medico_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
):
    """Devuelve las franjas de disponibilidad de un médico."""
    return disp_service.listar_disponibilidad(db, medico_id)


@router.post("", response_model=DisponibilidadOut, status_code=status.HTTP_201_CREATED)
async def crear_disponibilidad(
    datos: DisponibilidadCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(Rol.ADMIN)),
):
    """Define una franja de disponibilidad para un médico (solo ADMIN)."""
    try:
        franja = disp_service.crear_disponibilidad(
            db,
            medico_id=datos.medico_id,
            dia_semana=datos.dia_semana,
            hora_inicio=datos.hora_inicio,
            hora_fin=datos.hora_fin,
        )
    except disp_service.MedicoNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado") from None
    except disp_service.FranjaInvalida:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La hora de inicio debe ser anterior a la de fin",
        ) from None

    db.commit()
    return franja
