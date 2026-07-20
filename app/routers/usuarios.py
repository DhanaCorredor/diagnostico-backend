"""Router de gestión de personal/médicos (CRUD, solo ADMIN).

Regla: RECEPCIÓN no accede a la gestión de usuarios. Los pacientes se gestionan
en su propio router (aquí solo va el personal que hace login).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import requiere_rol
from app.db import get_db
from app.models import Rol
from app.schemas import UsuarioCreate, UsuarioDetalle, UsuarioUpdate
from app.services import usuarios as usr_service

# Toda la gestión de personal es solo para ADMIN (guarda a nivel de router).
router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(requiere_rol(Rol.ADMIN))],
)


@router.get("", response_model=list[UsuarioDetalle])
def listar_personal(db: Session = Depends(get_db)):
    """Lista el personal (ADMIN, RECEPCIÓN, MEDICO). No incluye pacientes."""
    return usr_service.listar_personal(db)


@router.get("/{usuario_id}", response_model=UsuarioDetalle)
def obtener_usuario(usuario_id: uuid.UUID, db: Session = Depends(get_db)):
    """Devuelve la ficha de un usuario del personal."""
    try:
        return usr_service.obtener_usuario(db, usuario_id)
    except usr_service.UsuarioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")


@router.post("", response_model=UsuarioDetalle, status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: UsuarioCreate, db: Session = Depends(get_db)):
    """Crea un usuario de personal (médico o staff), con su contraseña y especialidades."""
    try:
        usuario = usr_service.crear_usuario(
            db,
            nombre_completo=datos.nombre_completo,
            rol=datos.rol,
            email=datos.email,
            password=datos.password,
            matricula=datos.matricula,
            especialidades=datos.especialidades,
        )
    except usr_service.RolNoPermitido:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "No se puede crear un usuario con ese rol"
        )
    except usr_service.EmailDuplicado:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está en uso")
    except usr_service.EspecialidadNoEncontrada:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna especialidad no existe")

    db.commit()
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioDetalle)
def actualizar_usuario(
    usuario_id: uuid.UUID,
    datos: UsuarioUpdate,
    db: Session = Depends(get_db),
):
    """Edita un usuario del personal (solo los campos enviados)."""
    cambios = datos.model_dump(exclude_unset=True)
    try:
        usuario = usr_service.actualizar_usuario(db, usuario_id, cambios)
    except usr_service.UsuarioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    except usr_service.EmailDuplicado:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está en uso")
    except usr_service.EspecialidadNoEncontrada:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna especialidad no existe")

    db.commit()
    return usuario
