"""Router de catálogos de lectura: servicios (y más adelante especialidades, médicos).

Alimentan los desplegables del frontend al agendar. Solo requieren estar
autenticado (cualquier rol del personal), sin restricción por rol.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import usuario_actual
from app.db import get_db
from app.schemas import MedicoOut, ServicioOut
from app.services import catalogo as catalogo_service

router = APIRouter(tags=["catálogos"])


@router.get("/servicios", response_model=list[ServicioOut])
def listar_servicios(
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),  # solo exige estar autenticado
):
    """Devuelve el catálogo de servicios activos."""
    return catalogo_service.listar_servicios(db)


@router.get("/medicos", response_model=list[MedicoOut])
def listar_medicos(
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),  # solo exige estar autenticado
):
    """Devuelve los médicos activos con sus especialidades (para elegir al agendar)."""
    return catalogo_service.listar_medicos(db)
