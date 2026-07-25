"""Router de gestión del personal que hace login (ADMIN/RECEPCION/MEDICO): CRUD, solo ADMIN."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.enums import Role
from app.schemas import UserCreate, UserDetail, UserUpdate
from app.services import usuarios as usr_service

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)


@router.get("", response_model=list[UserDetail])
async def list_staff(db: Session = Depends(get_db)):
    """Lista el personal (ADMIN, RECEPCIÓN, MEDICO). No incluye pacientes."""
    return usr_service.list_staff(db)


@router.get("/{usuario_id}", response_model=UserDetail)
async def get_user(usuario_id: uuid.UUID, db: Session = Depends(get_db)):
    """Devuelve la ficha de un usuario del personal."""
    try:
        return usr_service.get_user(db, usuario_id)
    except usr_service.UserNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado") from None


@router.post("", response_model=UserDetail, status_code=status.HTTP_201_CREATED)
async def create_user(datos: UserCreate, db: Session = Depends(get_db)):
    """Crea un usuario de personal (médico o staff), con su contraseña y especialidades."""
    try:
        user = usr_service.create_user(
            db,
            nombre_completo=datos.nombre_completo,
            rol=datos.rol,
            email=datos.email,
            password=datos.password,
            matricula=datos.matricula,
            especialidades=datos.especialidades,
        )
    except usr_service.RoleNotAllowed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "No se puede crear un usuario con ese rol"
        ) from None
    except usr_service.DuplicateEmail:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está en uso") from None
    except usr_service.SpecialtyNotFound:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna especialidad no existe") from None
    except usr_service.DoctorOnlyData:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Especialidades y matrícula son solo para médicos"
        ) from None

    db.commit()
    return user


@router.delete("/{usuario_id}", response_model=UserDetail)
async def deactivate_user(usuario_id: uuid.UUID, db: Session = Depends(get_db)):
    """Da de baja (lógica) a un usuario: `activo=False`. Reactivar con PUT {"activo": true}."""
    try:
        user = usr_service.deactivate_user(db, usuario_id)
    except usr_service.UserNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado") from None

    db.commit()
    return user


@router.put("/{usuario_id}", response_model=UserDetail)
async def update_user(
    usuario_id: uuid.UUID,
    datos: UserUpdate,
    db: Session = Depends(get_db),
):
    """Edita un usuario del personal (solo los campos enviados)."""
    cambios = datos.model_dump(exclude_unset=True)
    try:
        user = usr_service.update_user(db, usuario_id, cambios)
    except usr_service.UserNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado") from None
    except usr_service.DuplicateEmail:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está en uso") from None
    except usr_service.SpecialtyNotFound:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna especialidad no existe") from None
    except usr_service.DoctorOnlyData:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Especialidades y matrícula son solo para médicos"
        ) from None

    db.commit()
    return user
