"""Router de citas: agendar, listar (agenda), editar/mover, cancelar y marcar asistencia."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.enums import Role
from app.models import User
from app.schemas import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentUpdate,
    AttendanceUpdate,
)
from app.services import appointments as appointment_service
from app.services.patients import AmbiguousPatients, PatientNotFound

router = APIRouter(prefix="/citas", tags=["citas"])

MAX_RANGE_DAYS = 60


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    datos: AppointmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.RECEPCION)),
):
    """Agenda una cita (recepción o admin) aplicando las reglas de negocio; cada fallo devuelve su código HTTP."""
    try:
        appointment = appointment_service.create_appointment(
            db,
            nombre_completo=datos.nombre_completo,
            edad=datos.edad,
            paciente_id=datos.paciente_id,
            medico_id=datos.medico_id,
            servicio_id=datos.servicio_id,
            starts_at=datos.starts_at,
            duracion_min=datos.duracion_min,
            creado_por_id=user.id,
            motivo=datos.motivo,
            permitir_sobrecupo=datos.permitir_sobrecupo,
        )
    except appointment_service.ServiceNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado") from None
    except appointment_service.DoctorNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado") from None
    except appointment_service.TimeNotAligned:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita debe empezar en :00, :15, :30 o :45",
        ) from None
    except appointment_service.AppointmentInThePast:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se puede agendar una cita en el pasado",
        ) from None
    except PatientNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    except AmbiguousPatients as e:
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
    except appointment_service.OutsideAvailability:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita cae fuera de la disponibilidad del médico",
        ) from None
    except appointment_service.Overlap:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El médico ya tiene una cita en ese horario",
        ) from None

    db.commit()
    return appointment


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    fecha: date | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    medico_id: uuid.UUID | None = None,
    incluir_canceladas: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.RECEPCION, Role.MEDICO)),
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
    if (hasta - desde).days > MAX_RANGE_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"El rango no puede superar los {MAX_RANGE_DAYS} días.",
        )
    if user.rol == Role.MEDICO:
        medico_id = user.id
    return appointment_service.list_appointments(
        db,
        desde=desde,
        hasta=hasta,
        medico_id=medico_id,
        incluir_canceladas=incluir_canceladas,
    )


@router.put("/{cita_id}", response_model=AppointmentOut)
async def edit_appointment(
    cita_id: uuid.UUID,
    datos: AppointmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.RECEPCION)),
):
    """Edita o mueve una cita activa (parcial, solo los campos enviados), revalidando las reglas. ADMIN o RECEPCIÓN."""
    try:
        appointment = appointment_service.edit_appointment(
            db,
            cita_id,
            medico_id=datos.medico_id,
            servicio_id=datos.servicio_id,
            starts_at=datos.starts_at,
            duracion_min=datos.duracion_min,
            motivo=datos.motivo,
            permitir_sobrecupo=datos.permitir_sobrecupo,
        )
    except appointment_service.AppointmentNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada") from None
    except appointment_service.AppointmentNotEditable:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La cita no se puede editar (ya está cancelada o cerrada)",
        ) from None
    except appointment_service.ServiceNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado") from None
    except appointment_service.DoctorNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado") from None
    except appointment_service.TimeNotAligned:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita debe empezar en :00, :15, :30 o :45",
        ) from None
    except appointment_service.AppointmentInThePast:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se puede mover una cita al pasado",
        ) from None
    except appointment_service.OutsideAvailability:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La cita cae fuera de la disponibilidad del médico",
        ) from None
    except appointment_service.Overlap:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El médico ya tiene una cita en ese horario",
        ) from None

    db.commit()
    return appointment


@router.post("/{cita_id}/cancelar", response_model=AppointmentOut)
async def cancel_appointment(
    cita_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.RECEPCION)),
):
    """Cancela una cita (libera el cupo). Solo ADMIN o RECEPCIÓN (el médico no cancela)."""
    try:
        appointment = appointment_service.cancel_appointment(db, cita_id)
    except appointment_service.AppointmentNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada") from None
    except appointment_service.AppointmentNotCancellable:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La cita no se puede cancelar (ya está cancelada o completada)",
        ) from None
    db.commit()
    return appointment


@router.post("/{cita_id}/asistencia", response_model=AppointmentOut)
async def mark_attendance(
    cita_id: uuid.UUID,
    datos: AttendanceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.RECEPCION)),
):
    """Marca una cita como **atendida** (COMPLETED) o **no-show** (NO_SHOW). Solo ADMIN o RECEPCIÓN."""
    try:
        appointment = appointment_service.mark_attendance(db, cita_id, datos.estado)
    except appointment_service.AppointmentNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada") from None
    except appointment_service.AppointmentNotActive:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo se puede marcar asistencia de una cita activa",
        ) from None
    db.commit()
    return appointment
