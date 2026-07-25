"""Router de citas: agendar, listar (agenda), editar/mover, cancelar y marcar asistencia."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import requiere_rol
from app.db import get_db
from app.enums import Role
from app.models import User
from app.schemas import AsistenciaUpdate, CitaCreate, CitaOut, CitaUpdate
from app.services import citas as citas_service
from app.services.pacientes import PacienteNoEncontrado, PacientesAmbiguos

router = APIRouter(prefix="/citas", tags=["citas"])

MAX_RANGO_DIAS = 60


@router.post("", response_model=CitaOut, status_code=status.HTTP_201_CREATED)
async def agendar_cita(
    datos: CitaCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(requiere_rol(Role.ADMIN, Role.RECEPCION)),
):
    """Agenda una cita (recepción o admin) aplicando las reglas de negocio; cada fallo devuelve su código HTTP."""
    try:
        cita = citas_service.crear_cita(
            db,
            nombre_completo=datos.nombre_completo,
            edad=datos.edad,
            paciente_id=datos.paciente_id,
            medico_id=datos.medico_id,
            servicio_id=datos.servicio_id,
            starts_at=datos.starts_at,
            duracion_min=datos.duracion_min,
            creado_por_id=usuario.id,
            motivo=datos.motivo,
            permitir_sobrecupo=datos.permitir_sobrecupo,
        )
    except citas_service.ServicioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado") from None
    except citas_service.MedicoNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado") from None
    except citas_service.HorarioNoAlineado:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita debe empezar en :00, :15, :30 o :45",
        ) from None
    except citas_service.CitaEnElPasado:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se puede agendar una cita en el pasado",
        ) from None
    except PacienteNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    except PacientesAmbiguos as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "mensaje": str(e),
                "candidatos": [
                    {
                        "id": str(c.id),
                        "nombre_completo": c.nombre_completo,
                        "edad": c.edad,
                    }
                    for c in e.candidatos
                ],
            },
        ) from None
    except citas_service.FueraDeDisponibilidad:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita cae fuera de la disponibilidad del médico",
        ) from None
    except citas_service.Solapamiento:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El médico ya tiene una cita en ese horario",
        ) from None

    db.commit()
    return cita


@router.get("", response_model=list[CitaOut])
async def listar_citas(
    fecha: date | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    medico_id: uuid.UUID | None = None,
    incluir_canceladas: bool = False,
    db: Session = Depends(get_db),
    usuario: User = Depends(requiere_rol(Role.ADMIN, Role.RECEPCION, Role.MEDICO)),
):
    """Lista la agenda de un día (`fecha`) o de un rango (`desde`..`hasta`), ambos incluidos.

    Un MÉDICO solo ve su propia agenda. Por defecto excluye las canceladas.
    """
    if fecha is not None:
        desde = hasta = fecha
    if desde is None or hasta is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Indica 'fecha' (un día) o 'desde' y 'hasta' (un rango).",
        )
    if hasta < desde:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "'hasta' no puede ser anterior a 'desde'.",
        )
    if (hasta - desde).days > MAX_RANGO_DIAS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"El rango no puede superar los {MAX_RANGO_DIAS} días.",
        )
    if usuario.rol == Role.MEDICO:
        medico_id = usuario.id
    return citas_service.listar_citas(
        db,
        desde=desde,
        hasta=hasta,
        medico_id=medico_id,
        incluir_canceladas=incluir_canceladas,
    )


@router.put("/{cita_id}", response_model=CitaOut)
async def editar_cita(
    cita_id: uuid.UUID,
    datos: CitaUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(requiere_rol(Role.ADMIN, Role.RECEPCION)),
):
    """Edita o mueve una cita activa (parcial, solo los campos enviados), revalidando las reglas. ADMIN o RECEPCIÓN."""
    try:
        cita = citas_service.editar_cita(
            db,
            cita_id,
            medico_id=datos.medico_id,
            servicio_id=datos.servicio_id,
            starts_at=datos.starts_at,
            duracion_min=datos.duracion_min,
            motivo=datos.motivo,
            permitir_sobrecupo=datos.permitir_sobrecupo,
        )
    except citas_service.CitaNoEncontrada:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada") from None
    except citas_service.CitaNoEditable:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La cita no se puede editar (ya está cancelada o cerrada)",
        ) from None
    except citas_service.ServicioNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado") from None
    except citas_service.MedicoNoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado") from None
    except citas_service.HorarioNoAlineado:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita debe empezar en :00, :15, :30 o :45",
        ) from None
    except citas_service.CitaEnElPasado:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se puede mover una cita al pasado",
        ) from None
    except citas_service.FueraDeDisponibilidad:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita cae fuera de la disponibilidad del médico",
        ) from None
    except citas_service.Solapamiento:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El médico ya tiene una cita en ese horario",
        ) from None

    db.commit()
    return cita


@router.post("/{cita_id}/cancelar", response_model=CitaOut)
async def cancelar_cita(
    cita_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(requiere_rol(Role.ADMIN, Role.RECEPCION)),
):
    """Cancela una cita (libera el cupo). Solo ADMIN o RECEPCIÓN (el médico no cancela)."""
    try:
        cita = citas_service.cancelar_cita(db, cita_id)
    except citas_service.CitaNoEncontrada:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada") from None
    except citas_service.CitaNoCancelable:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La cita no se puede cancelar (ya está cancelada o completada)",
        ) from None
    db.commit()
    return cita


@router.post("/{cita_id}/asistencia", response_model=CitaOut)
async def marcar_asistencia(
    cita_id: uuid.UUID,
    datos: AsistenciaUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(requiere_rol(Role.ADMIN, Role.RECEPCION)),
):
    """Marca una cita como **atendida** (COMPLETED) o **no-show** (NO_SHOW). Solo ADMIN o RECEPCIÓN."""
    try:
        cita = citas_service.marcar_asistencia(db, cita_id, datos.estado)
    except citas_service.CitaNoEncontrada:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada") from None
    except citas_service.CitaNoActiva:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo se puede marcar asistencia de una cita activa",
        ) from None
    db.commit()
    return cita
