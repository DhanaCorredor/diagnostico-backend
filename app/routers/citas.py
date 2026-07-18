"""Router de citas: agendar, listar (agenda) y cancelar."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import requiere_rol
from app.db import get_db
from app.models import Rol, Usuario
from app.schemas import CitaCreate, CitaOut
from app.services import citas as citas_service
from app.services.pacientes import PacientesAmbiguos

router = APIRouter(prefix="/citas", tags=["citas"])


@router.post("", response_model=CitaOut, status_code=status.HTTP_201_CREATED)
def agendar_cita(
    datos: CitaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(Rol.ADMIN, Rol.RECEPCION)),
):
    """Agenda una cita (la crea recepción o admin), aplicando todas las reglas de negocio.

    Cada regla que falla se traduce a un código HTTP claro. Si todo va bien, se hace commit.
    """
    try:
        cita = citas_service.crear_cita(
            db,
            nombre_completo=datos.nombre_completo,
            edad=datos.edad,
            medico_id=datos.medico_id,
            servicio_id=datos.servicio_id,
            starts_at=datos.starts_at,
            creado_por_id=usuario.id,
            motivo=datos.motivo,
            permitir_sobrecupo=datos.permitir_sobrecupo,
        )
    except citas_service.ServicioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado")
    except citas_service.MedicoNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado")
    except citas_service.HorarioNoAlineado:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita debe empezar en :00, :15, :30 o :45",
        )
    except PacientesAmbiguos as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except citas_service.FueraDeDisponibilidad:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita cae fuera de la disponibilidad del médico",
        )
    except citas_service.Solapamiento:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El médico ya tiene una cita en ese horario",
        )

    db.commit()  # todo válido: se confirma la transacción (cita + posible paciente nuevo)
    return cita


@router.get("", response_model=list[CitaOut])
def listar_citas(
    medico_id: uuid.UUID | None = None,
    fecha: date | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(Rol.ADMIN, Rol.RECEPCION, Rol.MEDICO)),
):
    """Lista la agenda de citas, con filtros opcionales por médico y por día.

    Un MÉDICO solo ve su propia agenda: se le fija el filtro a su id, ignorando
    cualquier medico_id que envíe. ADMIN y RECEPCIÓN ven la de cualquiera.
    """
    if usuario.rol == Rol.MEDICO:
        medico_id = usuario.id
    return citas_service.listar_citas(db, medico_id=medico_id, fecha=fecha)


@router.post("/{cita_id}/cancelar", response_model=CitaOut)
def cancelar_cita(
    cita_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(Rol.ADMIN, Rol.RECEPCION)),
):
    """Cancela una cita (libera el cupo). Solo ADMIN o RECEPCIÓN."""
    try:
        cita = citas_service.cancelar_cita(db, cita_id)
    except citas_service.CitaNoEncontrada:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada")
    except citas_service.CitaNoCancelable:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La cita no se puede cancelar (ya está cancelada o completada)",
        )
    db.commit()
    return cita
