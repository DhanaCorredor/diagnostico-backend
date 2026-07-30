"""Management router for the staff who log in (ADMIN/RECEPCION/MEDICO): CRUD, ADMIN only."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.enums import Role
from app.models import User
from app.schemas import UserCreate, UserDetail, UserErased, UserUpdate
from app.services import catalog as catalog_service
from app.services import users as user_service

router = APIRouter(
    prefix="/usuarios",
    tags=["users"],
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
    except catalog_service.SpecialtyNotFound:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna especialidad no existe") from None
    except user_service.DoctorOnlyData:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Especialidades y matrícula son solo para médicos"
        ) from None

    db.commit()
    return user


@router.delete("/{usuario_id}", response_model=UserErased)
async def erase_user(
    usuario_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
):
    """Erase a staff member for good, for someone who has left. **Irreversible**.

    To put someone aside temporarily and bring them back later, use `PUT {"activo": false}`
    instead: that one is reversible and keeps their data.
    """
    try:
        resultado, citas = user_service.erase_user(
            db, usuario_id, requested_by_id=user.id
        )
    except user_service.UserNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado") from None
    except user_service.CannotEraseSelf:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "No puedes eliminar tu propio usuario"
        ) from None
    except user_service.UserHasUpcomingAppointments as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ese médico tiene {e.count} cita(s) agendadas por delante. "
            "Reasígnalas o cancélalas antes de eliminarlo.",
        ) from None

    db.commit()
    return UserErased(resultado=resultado, citas_conservadas=citas)


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
    except catalog_service.SpecialtyNotFound:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna especialidad no existe") from None
    except user_service.DoctorOnlyData:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Especialidades y matrícula son solo para médicos"
        ) from None

    db.commit()
    return user
