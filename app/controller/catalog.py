"""Catalog router: reads of services/specialties/doctors (authenticated) and their management (ADMIN)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import current_user, require_role
from app.db import get_db
from app.enums import Role
from app.schemas import (
    DoctorOut,
    ServiceCreate,
    ServiceDetail,
    ServiceOut,
    ServiceUpdate,
    SpecialtyCreate,
    SpecialtyOut,
)
from app.services import catalog as catalog_service

router = APIRouter(tags=["catalog"])


@router.get("/servicios", response_model=list[ServiceOut])
async def list_services(
    medico_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _: object = Depends(current_user),
):
    """Return the catalog of active services; with `?medico_id=` it filters by the doctor's specialties."""
    return catalog_service.list_services(db, medico_id)


@router.get("/medicos", response_model=list[DoctorOut])
async def list_doctors(
    db: Session = Depends(get_db),
    _: object = Depends(current_user),
):
    """Return the active doctors with their specialties (to pick one when scheduling)."""
    return catalog_service.list_doctors(db)


@router.get("/especialidades", response_model=list[SpecialtyOut])
async def list_specialties(
    db: Session = Depends(get_db),
    _: object = Depends(current_user),
):
    """Return the catalog of medical specialties."""
    return catalog_service.list_specialties(db)


@router.post(
    "/servicios",
    response_model=ServiceDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_service(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ADMIN)),
):
    """Register a service in the catalog (ADMIN)."""
    try:
        service = catalog_service.create_service(
            db, nombre=data.nombre, categoria=data.categoria
        )
    except catalog_service.DuplicateName:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un servicio con ese nombre") from None

    db.commit()
    return service


@router.put("/servicios/{servicio_id}", response_model=ServiceDetail)
async def update_service(
    servicio_id: uuid.UUID,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ADMIN)),
):
    """Edit a service in the catalog (ADMIN). It can be deactivated without deleting it."""
    changes = data.model_dump(exclude_unset=True)
    try:
        service = catalog_service.update_service(db, servicio_id, changes)
    except catalog_service.ServiceNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado") from None
    except catalog_service.DuplicateName:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un servicio con ese nombre") from None

    db.commit()
    return service


@router.post(
    "/especialidades",
    response_model=SpecialtyOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_specialty(
    data: SpecialtyCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ADMIN)),
):
    """Register a medical specialty (ADMIN)."""
    try:
        specialty = catalog_service.create_specialty(db, nombre=data.nombre)
    except catalog_service.DuplicateName:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una especialidad con ese nombre"
        ) from None

    db.commit()
    return specialty
