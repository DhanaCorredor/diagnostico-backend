"""Esquemas Pydantic (entrada/salida de la API), agrupados por dominio."""
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.catalogo import (
    EspecialidadCreate,
    EspecialidadOut,
    MedicoOut,
    ServicioCreate,
    ServicioDetalle,
    ServicioOut,
    ServicioUpdate,
)
from app.schemas.cita import AsistenciaUpdate, CitaCreate, CitaOut, CitaUpdate
from app.schemas.disponibilidad import DisponibilidadCreate, DisponibilidadOut
from app.schemas.paciente import PacienteCreate, PacienteOut, PacienteUpdate
from app.schemas.usuario import UsuarioCreate, UsuarioDetalle, UsuarioOut, UsuarioUpdate

__all__ = [
    "AsistenciaUpdate",
    "CitaCreate",
    "CitaOut",
    "CitaUpdate",
    "DisponibilidadCreate",
    "DisponibilidadOut",
    "EspecialidadCreate",
    "EspecialidadOut",
    "LoginRequest",
    "MedicoOut",
    "PacienteCreate",
    "PacienteOut",
    "PacienteUpdate",
    "ServicioCreate",
    "ServicioDetalle",
    "ServicioOut",
    "ServicioUpdate",
    "TokenResponse",
    "UsuarioCreate",
    "UsuarioDetalle",
    "UsuarioOut",
    "UsuarioUpdate",
]
