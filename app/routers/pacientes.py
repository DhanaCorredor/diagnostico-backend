"""Router de pacientes: listar, ver ficha y editar. Gestión de recepción/admin."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import requiere_rol
from app.db import get_db
from app.models import Rol, Usuario
from app.schemas import PacienteOut, PacienteUpdate
from app.services import pacientes as pac_service

router = APIRouter(prefix="/pacientes", tags=["pacientes"])


@router.get("", response_model=list[PacienteOut])
def listar_pacientes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol(Rol.ADMIN, Rol.RECEPCION)),
):
    """Lista todos los pacientes (ADMIN o RECEPCIÓN)."""
    return pac_service.listar_pacientes(db)


@router.get("/{paciente_id}", response_model=PacienteOut)
def obtener_paciente(
    paciente_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol(Rol.ADMIN, Rol.RECEPCION)),
):
    """Devuelve la ficha de un paciente."""
    try:
        return pac_service.obtener_paciente(db, paciente_id)
    except pac_service.PacienteNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado")


@router.put("/{paciente_id}", response_model=PacienteOut)
def actualizar_paciente(
    paciente_id: uuid.UUID,
    datos: PacienteUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol(Rol.ADMIN, Rol.RECEPCION)),
):
    """Edita un paciente (ADMIN o RECEPCIÓN)."""
    try:
        paciente = pac_service.actualizar_paciente(
            db,
            paciente_id,
            nombre_completo=datos.nombre_completo,
            edad=datos.edad,
            cedula=datos.cedula,
            telefono=datos.telefono,
            fecha_nacimiento=datos.fecha_nacimiento,
        )
    except pac_service.PacienteNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado")
    except pac_service.CedulaDuplicada:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "La cédula ya pertenece a otra persona"
        )

    db.commit()
    return paciente
