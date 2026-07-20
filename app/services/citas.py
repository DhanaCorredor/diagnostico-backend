"""Lógica de negocio de las citas: duración, disponibilidad y anti-solapamiento.

Estas funciones son el núcleo del proyecto. Viven separadas de los endpoints
para poder probarlas de forma aislada.
"""

import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models import Cita, Disponibilidad, EstadoCita, Rol, Servicio, Usuario
from app.services.pacientes import buscar_o_crear_paciente

# La cita solo puede empezar en un minuto "de rejilla" (:00, :15, :30, :45).
# Cambiar este valor mueve la rejilla (p. ej. 10 o 20 min) sin tocar la lógica.
GRID_MINUTOS = 15


class ServicioNoEncontrado(Exception):
    """El servicio indicado no existe."""


class MedicoNoEncontrado(Exception):
    """El médico indicado no existe o no tiene rol MEDICO."""


class FueraDeDisponibilidad(Exception):
    """La cita cae fuera de la disponibilidad del médico (se puede forzar con sobrecupo)."""


class Solapamiento(Exception):
    """El médico ya tiene una cita activa que se cruza con este horario."""


class HorarioNoAlineado(Exception):
    """El inicio no cae en la rejilla de minutos permitida (:00, :15, :30, :45)."""


class CitaNoEncontrada(Exception):
    """No existe ninguna cita con ese id."""


class CitaNoCancelable(Exception):
    """La cita no se puede cancelar (ya está cancelada o completada)."""


def esta_alineado(starts_at: datetime) -> bool:
    """True si el inicio cae justo en la rejilla de GRID_MINUTOS y sin segundos sueltos.

    Ej. con rejilla de 15: 10:00 y 10:30 valen; 10:07 o 10:15:30 no.
    """
    return (
        starts_at.minute % GRID_MINUTOS == 0
        and starts_at.second == 0
        and starts_at.microsecond == 0
    )


def calcular_ends_at(starts_at: datetime, servicio: Servicio) -> datetime:
    """Calcula cuándo termina la cita: inicio + la duración que marca el servicio.

    La cita no guarda su propia duración; la hereda del servicio en este momento.
    Ej.: 10:00 + Consulta (45 min) -> 10:45.
    """
    return starts_at + timedelta(minutes=servicio.duracion_min)


def dentro_de_disponibilidad(
    db: Session, medico_id: uuid.UUID, starts_at: datetime, ends_at: datetime
) -> bool:
    """Comprueba si la cita cae ENTERA dentro de alguna franja del médico ese día.

    - Convierte el día de la semana a la convención del modelo (0=domingo).
    - La cita es válida si su inicio y su fin caben dentro de una misma franja.
    (Asume que la cita no cruza la medianoche, cierto en un centro de salud.)
    """
    dia_semana = (starts_at.weekday() + 1) % 7  # Python: lunes=0 -> modelo: domingo=0
    hora_inicio = starts_at.time()
    hora_fin = ends_at.time()

    franjas = (
        db.query(Disponibilidad)
        .filter(Disponibilidad.usuario_id == medico_id)
        .filter(Disponibilidad.dia_semana == dia_semana)
        .all()
    )
    return any(
        f.hora_inicio <= hora_inicio and hora_fin <= f.hora_fin for f in franjas
    )


def hay_solapamiento(
    db: Session,
    medico_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    excluir_cita_id: uuid.UUID | None = None,
) -> bool:
    """Indica si el médico ya tiene una cita ACTIVA que se cruza con este horario.

    Dos citas se cruzan si:  nueva.inicio < existente.fin  Y  nueva.fin > existente.inicio.
    - Solo cuentan las activas (SCHEDULED / CONFIRMED); una CANCELLED libera el hueco.
    - Citas pegadas (una acaba justo cuando empieza la otra) NO se solapan.
    - excluir_cita_id: al editar una cita, se ignora ella misma.
    """
    q = (
        db.query(Cita)
        .filter(Cita.medico_id == medico_id)
        .filter(Cita.estado.in_([EstadoCita.SCHEDULED, EstadoCita.CONFIRMED]))
        .filter(Cita.starts_at < ends_at)  # la existente empieza antes de que acabe la nueva
        .filter(Cita.ends_at > starts_at)  # y termina después de que empiece la nueva
    )
    if excluir_cita_id is not None:
        q = q.filter(Cita.id != excluir_cita_id)
    return db.query(q.exists()).scalar()


def crear_cita(
    db: Session,
    *,
    nombre_completo: str,
    edad: int,
    medico_id: uuid.UUID,
    servicio_id: uuid.UUID,
    starts_at: datetime,
    creado_por_id: uuid.UUID,
    motivo: str | None = None,
    permitir_sobrecupo: bool = False,
) -> Cita:
    """Orquesta las reglas y prepara la cita. Hace flush (no commit): el commit lo hace el endpoint.

    Orden: valida servicio y médico -> upsert del paciente -> calcula ends_at ->
    valida disponibilidad (salvo sobrecupo) -> valida anti-solapamiento (siempre).
    Lanza una excepción de dominio si alguna regla falla.
    """
    servicio = db.get(Servicio, servicio_id)
    if servicio is None:
        raise ServicioNoEncontrado()

    medico = db.get(Usuario, medico_id)
    if medico is None or medico.rol != Rol.MEDICO:
        raise MedicoNoEncontrado()

    # R0: el inicio debe caer en la rejilla de minutos (:00, :15, :30, :45).
    # Se valida antes de tocar al paciente para no crear datos por una hora inválida.
    if not esta_alineado(starts_at):
        raise HorarioNoAlineado()

    # R1: buscar o crear al paciente (puede lanzar PacientesAmbiguos)
    paciente = buscar_o_crear_paciente(db, nombre_completo, edad)

    # R2: la duración la marca el servicio
    ends_at = calcular_ends_at(starts_at, servicio)

    # R3: disponibilidad (salvo que recepción fuerce un sobrecupo)
    if not permitir_sobrecupo and not dentro_de_disponibilidad(
        db, medico_id, starts_at, ends_at
    ):
        raise FueraDeDisponibilidad()

    # R4: anti-solapamiento por médico (siempre se bloquea)
    if hay_solapamiento(db, medico_id, starts_at, ends_at):
        raise Solapamiento()

    cita = Cita(
        paciente_id=paciente.id,
        medico_id=medico_id,
        servicio_id=servicio_id,
        starts_at=starts_at,
        ends_at=ends_at,
        estado=EstadoCita.SCHEDULED,
        motivo=motivo,
        creado_por_id=creado_por_id,
    )
    db.add(cita)
    db.flush()  # asigna el id; el commit lo hace quien llama (el endpoint)
    return cita


def listar_citas(
    db: Session,
    *,
    desde: date,
    hasta: date,
    medico_id: uuid.UUID | None = None,
    incluir_canceladas: bool = False,
) -> list[Cita]:
    """Devuelve las citas del rango de días [desde, hasta] (ambos incluidos), ordenadas por inicio.

    - desde/hasta: acotan la consulta a un rango concreto; nunca se lista "todo el histórico".
    - medico_id: solo las de ese médico (recepción filtra; al médico se le fija el suyo).
    - incluir_canceladas: por defecto solo las vigentes; con True, también las canceladas.
    """
    inicio = datetime.combine(desde, time.min)
    fin = datetime.combine(hasta, time.min) + timedelta(days=1)  # exclusivo: fin del día 'hasta'
    q = db.query(Cita).filter(Cita.starts_at >= inicio).filter(Cita.starts_at < fin)
    if medico_id is not None:
        q = q.filter(Cita.medico_id == medico_id)
    if not incluir_canceladas:
        q = q.filter(Cita.estado != EstadoCita.CANCELLED)
    return q.order_by(Cita.starts_at).all()


def cancelar_cita(db: Session, cita_id: uuid.UUID) -> Cita:
    """Cancela una cita: pone su estado en CANCELLED y con ello libera el cupo.

    Solo se pueden cancelar citas activas (SCHEDULED/CONFIRMED); una ya cancelada
    o completada no. Hace flush (no commit): el commit lo hace el endpoint.
    """
    cita = db.get(Cita, cita_id)
    if cita is None:
        raise CitaNoEncontrada()
    if cita.estado not in (EstadoCita.SCHEDULED, EstadoCita.CONFIRMED):
        raise CitaNoCancelable()
    cita.estado = EstadoCita.CANCELLED
    db.flush()
    return cita
