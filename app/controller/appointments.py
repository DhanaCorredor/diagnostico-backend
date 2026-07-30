"""Appointment router: schedule, list (agenda), edit/move, cancel and mark attendance."""

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

router = APIRouter(prefix="/citas", tags=["appointments"])

MAX_RANGE_DAYS = 60


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.RECEPCION)),
):
    """Schedule an appointment (reception or admin) applying the business rules; each failure returns its HTTP code."""
    try:
        appointment = appointment_service.create_appointment(
            db,
            nombre_completo=data.nombre_completo,
            edad=data.edad,
            paciente_id=data.paciente_id,
            medico_id=data.medico_id,
            servicio_id=data.servicio_id,
            starts_at=data.starts_at,
            duracion_min=data.duracion_min,
            creado_por_id=user.id,
            motivo=data.motivo,
            permitir_sobrecupo=data.permitir_sobrecupo,
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
                    for c in e.candidates
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
    """List the agenda of one day (`fecha`) or of a range (`desde`..`hasta`), both included.

    A MEDICO only sees their own agenda. Cancelled appointments are excluded by default.
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


@router.get("/{cita_id}", response_model=AppointmentOut)
async def get_appointment(
    cita_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.RECEPCION, Role.MEDICO)),
):
    """Return one appointment. A MEDICO can only open their own."""
    try:
        appointment = appointment_service.get_appointment(db, cita_id)
    except appointment_service.AppointmentNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada") from None

    if user.rol == Role.MEDICO and appointment.medico_id != user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Solo puedes consultar tus propias citas"
        )
    return appointment


@router.put("/{cita_id}", response_model=AppointmentOut)
async def edit_appointment(
    cita_id: uuid.UUID,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.RECEPCION)),
):
    """Edit or move an active appointment (partial, only the fields sent), revalidating the rules. ADMIN or RECEPCION."""
    try:
        appointment = appointment_service.edit_appointment(
            db,
            cita_id,
            medico_id=data.medico_id,
            servicio_id=data.servicio_id,
            starts_at=data.starts_at,
            duracion_min=data.duracion_min,
            motivo=data.motivo,
            permitir_sobrecupo=data.permitir_sobrecupo,
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
    """Cancel an appointment (frees the slot). ADMIN or RECEPCION only (the doctor does not cancel)."""
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
    data: AttendanceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.RECEPCION)),
):
    """Mark an appointment as **attended** (COMPLETED) or **no-show** (NO_SHOW). ADMIN or RECEPCION only."""
    try:
        appointment = appointment_service.mark_attendance(db, cita_id, data.estado)
    except appointment_service.AppointmentNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada") from None
    except appointment_service.AppointmentNotActive:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo se puede marcar asistencia de una cita activa",
        ) from None
    db.commit()
    return appointment
