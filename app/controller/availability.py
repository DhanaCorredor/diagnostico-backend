"""Router de disponibilidad: ver las franjas de un médico (autenticado) y definirlas (ADMIN)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role, current_user
from app.db import get_db
from app.enums import Role
from app.models import User
from app.schemas import AvailabilityCreate, AvailabilityOut
from app.services import availability as availability_service

router = APIRouter(prefix="/disponibilidad", tags=["disponibilidad"])


@router.get("", response_model=list[AvailabilityOut])
async def list_availability(
    medico_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(current_user),
):
    """Devuelve las franjas de disponibilidad de un médico."""
    return availability_service.list_availability(db, medico_id)


@router.post("", response_model=AvailabilityOut, status_code=status.HTTP_201_CREATED)
async def create_availability(
    datos: AvailabilityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
):
    """Define una franja de disponibilidad para un médico (solo ADMIN)."""
    try:
        slot = availability_service.create_availability(
            db,
            medico_id=datos.medico_id,
            dia_semana=datos.dia_semana,
            hora_inicio=datos.hora_inicio,
            hora_fin=datos.hora_fin,
        )
    except availability_service.DoctorNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado") from None
    except availability_service.InvalidSlot:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La hora de inicio debe ser anterior a la de fin",
        ) from None

    db.commit()
    return slot
