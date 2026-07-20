"""Router de pacientes: listar, ver ficha y editar. Gestión de recepción/admin."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import requiere_rol
from app.db import get_db
from app.models import Rol
from app.schemas import PacienteOut, PacienteUpdate
from app.services import pacientes as pac_service

# Toda la gestión de pacientes es solo para ADMIN y RECEPCIÓN (guarda a nivel de router).
router = APIRouter(
    prefix="/pacientes",
    tags=["pacientes"],
    dependencies=[Depends(requiere_rol(Rol.ADMIN, Rol.RECEPCION))],
)


@router.get("", response_model=list[PacienteOut])
def listar_pacientes(db: Session = Depends(get_db)):
    """Lista todos los pacientes."""
    return pac_service.listar_pacientes(db)


@router.get("/{paciente_id}", response_model=PacienteOut)
def obtener_paciente(paciente_id: uuid.UUID, db: Session = Depends(get_db)):
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
):
    """Edita un paciente: solo se actualizan los campos enviados (no borra los omitidos)."""
    cambios = datos.model_dump(exclude_unset=True)
    try:
        paciente = pac_service.actualizar_paciente(db, paciente_id, cambios)
    except pac_service.PacienteNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado")
    except pac_service.CedulaDuplicada:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "La cédula ya pertenece a otra persona"
        )

    db.commit()
    return paciente
