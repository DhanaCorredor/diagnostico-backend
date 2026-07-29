"""Patient router: list, view details and edit. Managed by reception/admin."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.enums import Role
from app.schemas import AppointmentOut, PatientCreate, PatientOut, PatientUpdate
from app.services import appointments as appointment_service
from app.services import patients as patient_service

router = APIRouter(
    prefix="/pacientes",
    tags=["patients"],
    dependencies=[Depends(require_role(Role.ADMIN, Role.RECEPCION))],
)


@router.get("", response_model=list[PatientOut])
async def list_patients(db: Session = Depends(get_db)):
    """List the active patients."""
    return patient_service.list_patients(db)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    """Register a patient manually (without scheduling an appointment)."""
    try:
        patient = patient_service.create_patient(db, data.model_dump())
    except patient_service.DuplicateNationalId:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "La cédula ya pertenece a otra persona"
        ) from None
    db.commit()
    return patient


@router.get("/{paciente_id}", response_model=PatientOut)
async def get_patient(paciente_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return the details of a patient."""
    try:
        return patient_service.get_patient(db, paciente_id)
    except patient_service.PatientNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None


@router.get("/{paciente_id}/citas", response_model=list[AppointmentOut])
async def appointment_history(paciente_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return the appointment history of a patient (from the most recent to the oldest)."""
    try:
        patient_service.get_patient(db, paciente_id)
    except patient_service.PatientNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    return appointment_service.list_patient_appointments(db, paciente_id)


@router.put("/{paciente_id}", response_model=PatientOut)
async def update_patient(
    paciente_id: uuid.UUID,
    data: PatientUpdate,
    db: Session = Depends(get_db),
):
    """Edit a patient: only the fields sent are updated (omitted ones are not cleared)."""
    changes = data.model_dump(exclude_unset=True)
    try:
        patient = patient_service.update_patient(db, paciente_id, changes)
    except patient_service.PatientNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    except patient_service.DuplicateNationalId:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "La cédula ya pertenece a otra persona"
        ) from None

    db.commit()
    return patient


@router.delete("/{paciente_id}", response_model=PatientOut)
async def deactivate_patient(paciente_id: uuid.UUID, db: Session = Depends(get_db)):
    """Soft-delete a patient: `activo=False`. It leaves the list (which only shows active ones)."""
    try:
        patient = patient_service.deactivate_patient(db, paciente_id)
    except patient_service.PatientNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    db.commit()
    return patient
