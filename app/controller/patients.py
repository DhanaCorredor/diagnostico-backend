"""Patient router: list, view details and edit. Managed by reception/admin."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.controller.errors import as_http
from app.db import get_db
from app.enums import Role
from app.schemas import AppointmentOut, PatientCreate, PatientErased, PatientOut, PatientUpdate
from app.services import appointments as appointment_service
from app.services import patients as patient_service

router = APIRouter(
    prefix="/pacientes",
    tags=["patients"],
    dependencies=[Depends(require_role(Role.ADMIN, Role.RECEPCION))],
)

# Same failure, same answer, whichever endpoint hit it.
PATIENT_ERRORS = {
    patient_service.PatientNotFound: (
        status.HTTP_404_NOT_FOUND,
        "Paciente no encontrado",
    ),
    patient_service.DuplicateNationalId: (
        status.HTTP_409_CONFLICT,
        "La cédula ya pertenece a otra persona",
    ),
}


@router.get("", response_model=list[PatientOut])
async def list_patients(db: Session = Depends(get_db)):
    """List the active patients."""
    return patient_service.list_patients(db)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    """Register a patient manually (without scheduling an appointment)."""
    with as_http(PATIENT_ERRORS):
        patient = patient_service.create_patient(db, data.model_dump())
    db.commit()
    return patient


@router.get("/{paciente_id}", response_model=PatientOut)
async def get_patient(paciente_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return the details of a patient."""
    with as_http(PATIENT_ERRORS):
        return patient_service.get_patient(db, paciente_id)


@router.get("/{paciente_id}/citas", response_model=list[AppointmentOut])
async def appointment_history(paciente_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return the appointment history of a patient (from the most recent to the oldest)."""
    with as_http(PATIENT_ERRORS):
        patient_service.get_patient(db, paciente_id)
    return appointment_service.list_patient_appointments(db, paciente_id)


@router.put("/{paciente_id}", response_model=PatientOut)
async def update_patient(
    paciente_id: uuid.UUID,
    data: PatientUpdate,
    db: Session = Depends(get_db),
):
    """Edit a patient: only the fields sent are updated (omitted ones are not cleared)."""
    changes = data.model_dump(exclude_unset=True)
    with as_http(PATIENT_ERRORS):
        patient = patient_service.update_patient(db, paciente_id, changes)

    db.commit()
    return patient


@router.delete("/{paciente_id}", response_model=PatientErased)
async def erase_patient(paciente_id: uuid.UUID, db: Session = Depends(get_db)):
    """Erase a patient's personal data for good. **Irreversible**, there is no reactivation.

    If the patient has no appointments the record is deleted outright; if it has, the personal
    data is wiped and the appointments are kept as an unidentified record of the visit.
    """
    with as_http(PATIENT_ERRORS):
        resultado, citas = patient_service.erase_patient(db, paciente_id)
    db.commit()
    return PatientErased(resultado=resultado, citas_conservadas=citas)
