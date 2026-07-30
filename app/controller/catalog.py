"""Catalog router: reads of services/specialties/doctors (authenticated) and their management (ADMIN)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import current_user, require_role
from app.controller.errors import as_http
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
    SpecialtyUpdate,
)
from app.services import catalog as catalog_service

router = APIRouter(tags=["catalog"])

# The same exception means different things depending on what is being managed, so there are two
# maps: for a service, `SpecialtyNotFound` is "one of the ones you sent"; for a specialty, itself.
SERVICE_ERRORS = {
    catalog_service.ServiceNotFound: (
        status.HTTP_404_NOT_FOUND,
        "Servicio no encontrado",
    ),
    catalog_service.SpecialtyNotFound: (
        status.HTTP_404_NOT_FOUND,
        "Alguna especialidad no existe",
    ),
    catalog_service.DuplicateName: (
        status.HTTP_409_CONFLICT,
        "Ya existe un servicio con ese nombre",
    ),
}

SPECIALTY_ERRORS = {
    catalog_service.SpecialtyNotFound: (
        status.HTTP_404_NOT_FOUND,
        "Especialidad no encontrada",
    ),
    catalog_service.DuplicateName: (
        status.HTTP_409_CONFLICT,
        "Ya existe una especialidad con ese nombre",
    ),
}


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
    with as_http(SERVICE_ERRORS):
        service = catalog_service.create_service(
            db, nombre=data.nombre, categoria=data.categoria
        )

    db.commit()
    return service


@router.put("/servicios/{servicio_id}", response_model=ServiceDetail)
async def update_service(
    servicio_id: uuid.UUID,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ADMIN)),
):
    """Edit a service in the catalog (ADMIN), including the specialties that offer it."""
    changes = data.model_dump(exclude_unset=True)
    with as_http(SERVICE_ERRORS):
        service = catalog_service.update_service(db, servicio_id, changes)

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
    with as_http(SPECIALTY_ERRORS):
        specialty = catalog_service.create_specialty(db, nombre=data.nombre)

    db.commit()
    return specialty


@router.put("/especialidades/{especialidad_id}", response_model=SpecialtyOut)
async def update_specialty(
    especialidad_id: uuid.UUID,
    data: SpecialtyUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ADMIN)),
):
    """Rename a medical specialty (ADMIN)."""
    with as_http(SPECIALTY_ERRORS):
        specialty = catalog_service.update_specialty(
            db, especialidad_id, nombre=data.nombre
        )

    db.commit()
    return specialty


@router.delete("/especialidades/{especialidad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_specialty(
    especialidad_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ADMIN)),
):
    """Remove a medical specialty, unless doctors or services still use it (ADMIN)."""
    try:
        with as_http(SPECIALTY_ERRORS):
            catalog_service.delete_specialty(db, especialidad_id)
    except catalog_service.SpecialtyInUse as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"La especialidad la usan {e.doctors} médico(s) y {e.services} servicio(s). "
            "Desvincúlalos antes de eliminarla.",
        ) from None

    db.commit()


@router.delete("/servicios/{servicio_id}", response_model=ServiceDetail)
async def deactivate_service(
    servicio_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(Role.ADMIN)),
):
    """Soft-delete a service (ADMIN): it leaves the catalog but keeps explaining old appointments."""
    with as_http(SERVICE_ERRORS):
        service = catalog_service.deactivate_service(db, servicio_id)

    db.commit()
    return service
