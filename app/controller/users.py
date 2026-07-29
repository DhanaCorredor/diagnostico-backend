"""Management router for the staff who log in (ADMIN/RECEPCION/MEDICO): CRUD, ADMIN only."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.enums import Role
from app.schemas import UserCreate, UserDetail, UserUpdate
from app.services import users as user_service

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)


@router.get("", response_model=list[UserDetail])
async def list_staff(db: Session = Depends(get_db)):
    """List the staff (ADMIN, RECEPCION, MEDICO). Patients are not included."""
    return user_service.list_staff(db)


@router.get("/{usuario_id}", response_model=UserDetail)
async def get_user(usuario_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return the details of a staff user."""
    try:
        return user_service.get_user(db, usuario_id)
    except user_service.UserNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado") from None


@router.post("", response_model=UserDetail, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """Create a staff user (doctor or staff), with their password and specialties."""
    try:
        user = user_service.create_user(
            db,
            nombre_completo=data.nombre_completo,
            rol=data.rol,
            email=data.email,
            password=data.password,
            matricula=data.matricula,
            especialidades=data.especialidades,
        )
    except user_service.RoleNotAllowed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "No se puede crear un usuario con ese rol"
        ) from None
    except user_service.DuplicateEmail:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está en uso") from None
    except user_service.SpecialtyNotFound:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna especialidad no existe") from None
    except user_service.DoctorOnlyData:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Especialidades y matrícula son solo para médicos"
        ) from None

    db.commit()
    return user


@router.delete("/{usuario_id}", response_model=UserDetail)
async def deactivate_user(usuario_id: uuid.UUID, db: Session = Depends(get_db)):
    """Soft-delete a user: `activo=False`. Reactivate with PUT {"activo": true}."""
    try:
        user = user_service.deactivate_user(db, usuario_id)
    except user_service.UserNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado") from None

    db.commit()
    return user


@router.put("/{usuario_id}", response_model=UserDetail)
async def update_user(
    usuario_id: uuid.UUID,
    data: UserUpdate,
    db: Session = Depends(get_db),
):
    """Edit a staff user (only the fields sent)."""
    changes = data.model_dump(exclude_unset=True)
    try:
        user = user_service.update_user(db, usuario_id, changes)
    except user_service.UserNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado") from None
    except user_service.DuplicateEmail:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está en uso") from None
    except user_service.SpecialtyNotFound:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna especialidad no existe") from None
    except user_service.DoctorOnlyData:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Especialidades y matrícula son solo para médicos"
        ) from None

    db.commit()
    return user
