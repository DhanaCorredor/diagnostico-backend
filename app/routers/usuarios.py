"""Router de usuarios. En el MVP: listado, solo para ADMIN.

Implementa la regla RN: RECEPCIÓN no accede a la gestión de usuarios.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import requiere_rol
from app.db import get_db
from app.models import Rol, Usuario
from app.schemas import UsuarioOut

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get(
    "",
    response_model=list[UsuarioOut],
    dependencies=[Depends(requiere_rol(Rol.ADMIN))],  # guarda: solo ADMIN
)
def listar_usuarios(db: Session = Depends(get_db)):
    """Devuelve todos los usuarios. Requiere token de un usuario con rol ADMIN."""
    return db.query(Usuario).all()
