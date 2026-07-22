"""Router de catálogos: lectura (servicios, especialidades, médicos) y gestión (ADMIN).

Las lecturas alimentan los desplegables del frontend al agendar y solo requieren
estar autenticado (cualquier rol del personal). La gestión (alta/edición de
servicios y alta de especialidades) es solo para ADMIN.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import requiere_rol, usuario_actual
from app.db import get_db
from app.models import Rol
from app.schemas import (
    EspecialidadCreate,
    EspecialidadOut,
    MedicoOut,
    ServicioCreate,
    ServicioDetalle,
    ServicioOut,
    ServicioUpdate,
)
from app.services import catalogo as catalogo_service

router = APIRouter(tags=["catálogos"])


@router.get("/servicios", response_model=list[ServicioOut])
def listar_servicios(
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
):
    """Devuelve el catálogo de servicios activos."""
    return catalogo_service.listar_servicios(db)


@router.get("/medicos", response_model=list[MedicoOut])
def listar_medicos(
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
):
    """Devuelve los médicos activos con sus especialidades (para elegir al agendar)."""
    return catalogo_service.listar_medicos(db)


@router.get("/especialidades", response_model=list[EspecialidadOut])
def listar_especialidades(
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
):
    """Devuelve el catálogo de especialidades médicas."""
    return catalogo_service.listar_especialidades(db)


@router.post(
    "/servicios",
    response_model=ServicioDetalle,
    status_code=status.HTTP_201_CREATED,
)
def crear_servicio(
    datos: ServicioCreate,
    db: Session = Depends(get_db),
    _: object = Depends(requiere_rol(Rol.ADMIN)),
):
    """Da de alta un servicio en el catálogo (ADMIN)."""
    try:
        servicio = catalogo_service.crear_servicio(
            db, nombre=datos.nombre, categoria=datos.categoria
        )
    except catalogo_service.NombreDuplicado:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un servicio con ese nombre") from None

    db.commit()
    return servicio


@router.put("/servicios/{servicio_id}", response_model=ServicioDetalle)
def actualizar_servicio(
    servicio_id: uuid.UUID,
    datos: ServicioUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(requiere_rol(Rol.ADMIN)),
):
    """Edita un servicio del catálogo (ADMIN). Permite desactivarlo sin borrarlo."""
    cambios = datos.model_dump(exclude_unset=True)
    try:
        servicio = catalogo_service.actualizar_servicio(db, servicio_id, cambios)
    except catalogo_service.ServicioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado") from None
    except catalogo_service.NombreDuplicado:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un servicio con ese nombre") from None

    db.commit()
    return servicio


@router.post(
    "/especialidades",
    response_model=EspecialidadOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_especialidad(
    datos: EspecialidadCreate,
    db: Session = Depends(get_db),
    _: object = Depends(requiere_rol(Rol.ADMIN)),
):
    """Da de alta una especialidad médica (ADMIN)."""
    try:
        especialidad = catalogo_service.crear_especialidad(db, nombre=datos.nombre)
    except catalogo_service.NombreDuplicado:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una especialidad con ese nombre"
        ) from None

    db.commit()
    return especialidad
