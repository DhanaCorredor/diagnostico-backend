"""Availability router: view a doctor's slots (authenticated) and define them (ADMIN)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import current_user, require_role
from app.controller.errors import as_http
from app.db import get_db
from app.enums import Role
from app.models import User
from app.schemas import AvailabilityCreate, AvailabilityOut, AvailabilityUpdate
from app.services import availability as availability_service

router = APIRouter(prefix="/disponibilidad", tags=["availability"])

# Same failure, same answer, whichever endpoint hit it.
SLOT_ERRORS = {
    availability_service.DoctorNotFound: (
        status.HTTP_404_NOT_FOUND,
        "Médico no encontrado",
    ),
    availability_service.SlotNotFound: (
        status.HTTP_404_NOT_FOUND,
        "Franja no encontrada",
    ),
    availability_service.InvalidSlot: (
        status.HTTP_400_BAD_REQUEST,
        "La hora de inicio debe ser anterior a la de fin",
    ),
    availability_service.OverlappingSlot: (
        status.HTTP_409_CONFLICT,
        "El médico ya tiene una franja que se cruza con esa ese día",
    ),
}


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
    _: User = Depends(require_role(Role.ADMIN)),
):
    """Define an availability slot for a doctor (ADMIN only)."""
    with as_http(SLOT_ERRORS):
        slot = availability_service.create_availability(
            db,
            medico_id=data.medico_id,
            dia_semana=data.dia_semana,
            hora_inicio=data.hora_inicio,
            hora_fin=data.hora_fin,
        )

    db.commit()
    return slot


@router.put("/{franja_id}", response_model=AvailabilityOut)
async def update_availability(
    franja_id: uuid.UUID,
    data: AvailabilityUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    """Edit a slot (partial, only the fields sent). The doctor is not changed. ADMIN only."""
    try:
        with as_http(SLOT_ERRORS):
            slot = availability_service.update_availability(
                db,
                franja_id=franja_id,
                dia_semana=data.dia_semana,
                hora_inicio=data.hora_inicio,
                hora_fin=data.hora_fin,
            )
    except availability_service.StrandedAppointments as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Hay {e.count} cita(s) agendadas que quedarían fuera del horario. "
            "Muévelas o cancélalas antes de reducir la franja.",
        ) from None

    db.commit()
    return slot


@router.delete("/{franja_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability(
    franja_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    """Remove a slot, unless it still holds booked appointments. ADMIN only."""
    try:
        with as_http(SLOT_ERRORS):
            availability_service.delete_availability(db, franja_id)
    except availability_service.StrandedAppointments as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Hay {e.count} cita(s) agendadas en esa franja. "
            "Muévelas o cancélalas antes de eliminarla.",
        ) from None

    db.commit()
