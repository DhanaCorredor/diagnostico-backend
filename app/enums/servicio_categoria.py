"""Categoría de un servicio del catálogo."""
import enum


class ServicioCategoria(str, enum.Enum):
    CONSULTA = "CONSULTA"
    ECOGRAFIA = "ECOGRAFIA"
    DOPPLER = "DOPPLER"
    ESTUDIO_CARDIACO = "ESTUDIO_CARDIACO"
    PROMOCION = "PROMOCION"
    OTRO = "OTRO"
