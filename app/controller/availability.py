"""Availability router: view a doctor's slots (authenticated) and define them (ADMIN)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import current_user, require_role
from app.db import get_db
from app.enums import Role
from app.models import User
from app.schemas import AvailabilityCreate, AvailabilityOut
from app.services import availability as availability_service

router = APIRouter(prefix="/disponibilidad", tags=["availability"])


@router.get("", response_model=list[AvailabilityOut])
async def list_availability(
    medico_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(current_user),
):
    """Return the availability slots of a doctor."""
    return availability_service.list_availability(db, medico_id)


@router.post("", response_model=AvailabilityOut, status_code=status.HTTP_201_CREATED)
async def create_availability(
    data: AvailabilityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
):
    """Define an availability slot for a doctor (ADMIN only)."""
    try:
        slot = availability_service.create_availability(
            db,
            medico_id=data.medico_id,
            dia_semana=data.dia_semana,
            hora_inicio=data.hora_inicio,
            hora_fin=data.hora_fin,
        )
    except availability_service.DoctorNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado") from None
    except availability_service.InvalidSlot:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La hora de inicio debe ser anterior a la de fin",
        ) from None
    except availability_service.OverlappingSlot:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El médico ya tiene una franja que se cruza con esa ese día",
        ) from None

    db.commit()
    return slot
