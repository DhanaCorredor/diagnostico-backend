"""Lógica de negocio de las citas: duración, disponibilidad y anti-solapamiento.

Estas funciones son el núcleo del proyecto. Viven separadas de los endpoints
para poder probarlas de forma aislada.
"""

import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Cita, Disponibilidad, EstadoCita, Rol, Servicio, Usuario
from app.services.pacientes import buscar_o_crear_paciente, obtener_paciente

GRID_MINUTOS = 15

ZONA_CENTRO = timezone(timedelta(hours=-4))


def ahora_centro() -> datetime:
    """Hora actual en la zona del centro (UTC-4), naive (sin tzinfo)."""
    return datetime.now(ZONA_CENTRO).replace(tzinfo=None)


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


class CitaEnElPasado(Exception):
    """El inicio de la cita ya pasó; no se puede agendar en el pasado."""


class CitaNoEncontrada(Exception):
    """No existe ninguna cita con ese id."""


class CitaNoCancelable(Exception):
    """La cita no se puede cancelar (ya está cancelada o completada)."""


class CitaNoActiva(Exception):
    """La cita no está activa (SCHEDULED/CONFIRMED): no se puede marcar su asistencia."""


class CitaNoEditable(Exception):
    """La cita no está activa (ya cancelada o cerrada): no se puede editar ni mover."""


def esta_alineado(starts_at: datetime) -> bool:
    """True si el inicio cae justo en la rejilla de GRID_MINUTOS y sin segundos sueltos.

    Ej. con rejilla de 15: 10:00 y 10:30 valen; 10:07 o 10:15:30 no.
    """
    return (
        starts_at.minute % GRID_MINUTOS == 0
        and starts_at.second == 0
        and starts_at.microsecond == 0
    )


def calcular_ends_at(starts_at: datetime, duracion_min: int) -> datetime:
    """Calcula cuándo termina la cita: inicio + la duración elegida (en minutos).

    La duración la elige recepción al agendar (ya no la marca el servicio).
    Ej.: 10:00 + 45 min -> 10:45.
    """
    return starts_at + timedelta(minutes=duracion_min)


def dentro_de_disponibilidad(
    db: Session, medico_id: uuid.UUID, starts_at: datetime, ends_at: datetime
) -> bool:
    """Comprueba si la cita cae ENTERA dentro de alguna franja del médico ese día.

    - Convierte el día de la semana a la convención del modelo (0=domingo).
    - La cita es válida si su inicio y su fin caben dentro de una misma franja.
    (Asume que la cita no cruza la medianoche, cierto en un centro de salud.)
    """
    dia_semana = (starts_at.weekday() + 1) % 7
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
    - excluir_cita_id: al mover una cita, se excluye ella misma (si no, chocaría consigo misma).
    """
    q = (
        db.query(Cita)
        .filter(Cita.medico_id == medico_id)
        .filter(Cita.estado.in_([EstadoCita.SCHEDULED, EstadoCita.CONFIRMED]))
        .filter(Cita.starts_at < ends_at)
        .filter(Cita.ends_at > starts_at)
    )
    if excluir_cita_id is not None:
        q = q.filter(Cita.id != excluir_cita_id)
    return db.query(q.exists()).scalar()


def _validar_servicio_medico_y_rejilla(
    db: Session,
    *,
    servicio_id: uuid.UUID,
    medico_id: uuid.UUID,
    starts_at: datetime,
) -> None:
    """Valida las reglas comunes de identidad y encaje horario (crear y editar cita).

    - El servicio debe existir y estar activo (uno desactivado no es agendable).
    - El médico debe existir, tener rol MEDICO y estar activo (uno de baja no es agendable).
    - El inicio debe caer en la rejilla de minutos (:00, :15, :30, :45).
    Lanza la excepción de dominio correspondiente si algo falla.
    """
    servicio = db.get(Servicio, servicio_id)
    if servicio is None or not servicio.activo:
        raise ServicioNoEncontrado()
    medico = db.get(Usuario, medico_id)
    if medico is None or medico.rol != Rol.MEDICO or not medico.activo:
        raise MedicoNoEncontrado()
    if not esta_alineado(starts_at):
        raise HorarioNoAlineado()


def _validar_hueco(
    db: Session,
    *,
    medico_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    permitir_sobrecupo: bool,
    excluir_cita_id: uuid.UUID | None = None,
) -> None:
    """Valida que el hueco esté libre (crear y editar cita).

    - Disponibilidad: la cita debe caer dentro de una franja del médico (salvo sobrecupo).
    - Anti-solapamiento: el médico no puede tener otra cita activa que se cruce
      (al editar se excluye la propia cita con `excluir_cita_id`).
    """
    if not permitir_sobrecupo and not dentro_de_disponibilidad(
        db, medico_id, starts_at, ends_at
    ):
        raise FueraDeDisponibilidad()
    if hay_solapamiento(db, medico_id, starts_at, ends_at, excluir_cita_id=excluir_cita_id):
        raise Solapamiento()


def crear_cita(
    db: Session,
    *,
    nombre_completo: str,
    edad: int,
    paciente_id: uuid.UUID | None = None,
    medico_id: uuid.UUID,
    servicio_id: uuid.UUID,
    starts_at: datetime,
    duracion_min: int,
    creado_por_id: uuid.UUID,
    motivo: str | None = None,
    permitir_sobrecupo: bool = False,
    ahora: datetime | None = None,
) -> Cita:
    """Orquesta las reglas y prepara la cita. Hace flush (no commit): el commit lo hace el endpoint.

    Orden: valida servicio y médico -> rejilla y no-pasado -> upsert del paciente ->
    calcula ends_at -> valida disponibilidad (salvo sobrecupo) -> valida anti-solapamiento.
    Lanza una excepción de dominio si alguna regla falla.

    `ahora` se inyecta (por defecto la hora actual) para poder probar la regla del pasado.
    """
    _validar_servicio_medico_y_rejilla(
        db, servicio_id=servicio_id, medico_id=medico_id, starts_at=starts_at
    )

    if ahora is None:
        ahora = ahora_centro()
    if starts_at < ahora:
        raise CitaEnElPasado()

    if paciente_id is not None:
        paciente = obtener_paciente(db, paciente_id)
    else:
        paciente = buscar_o_crear_paciente(db, nombre_completo, edad)

    ends_at = calcular_ends_at(starts_at, duracion_min)

    _validar_hueco(
        db,
        medico_id=medico_id,
        starts_at=starts_at,
        ends_at=ends_at,
        permitir_sobrecupo=permitir_sobrecupo,
    )

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
    db.flush()
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
    fin = datetime.combine(hasta, time.min) + timedelta(days=1)
    q = db.query(Cita).filter(Cita.starts_at >= inicio).filter(Cita.starts_at < fin)
    if medico_id is not None:
        q = q.filter(Cita.medico_id == medico_id)
    if not incluir_canceladas:
        q = q.filter(Cita.estado != EstadoCita.CANCELLED)
    return q.order_by(Cita.starts_at).all()


def listar_citas_de_paciente(db: Session, paciente_id: uuid.UUID) -> list[Cita]:
    """Historial de citas de un paciente: todas las suyas, de la más reciente a la más antigua.

    A diferencia de `listar_citas` (agenda por día/rango), aquí no se acota por fecha
    ni se filtran estados: es el historial completo del paciente (incluidas canceladas).
    """
    return (
        db.query(Cita)
        .filter(Cita.paciente_id == paciente_id)
        .order_by(Cita.starts_at.desc())
        .all()
    )


def _obtener_cita_activa(
    db: Session, cita_id: uuid.UUID, exc_no_activa: type[Exception]
) -> Cita:
    """Devuelve la cita si existe y está activa (SCHEDULED/CONFIRMED).

    Lanza CitaNoEncontrada si no existe, o `exc_no_activa` si no está activa
    (ya cancelada, completada o no-show).
    """
    cita = db.get(Cita, cita_id)
    if cita is None:
        raise CitaNoEncontrada()
    if cita.estado not in (EstadoCita.SCHEDULED, EstadoCita.CONFIRMED):
        raise exc_no_activa()
    return cita


def cancelar_cita(db: Session, cita_id: uuid.UUID) -> Cita:
    """Cancela una cita: pone su estado en CANCELLED y con ello libera el cupo.

    Solo se pueden cancelar citas activas; una ya cancelada o completada no.
    Hace flush (no commit): el commit lo hace el endpoint.
    """
    cita = _obtener_cita_activa(db, cita_id, CitaNoCancelable)
    cita.estado = EstadoCita.CANCELLED
    db.flush()
    return cita


def marcar_asistencia(db: Session, cita_id: uuid.UUID, estado: EstadoCita) -> Cita:
    """Marca una cita como atendida (COMPLETED) o no-show (NO_SHOW).

    Solo sobre citas activas; una cancelada o ya cerrada no.
    Hace flush (no commit): el commit lo hace el endpoint.
    """
    cita = _obtener_cita_activa(db, cita_id, CitaNoActiva)
    cita.estado = estado
    db.flush()
    return cita


def editar_cita(
    db: Session,
    cita_id: uuid.UUID,
    *,
    medico_id: uuid.UUID | None = None,
    servicio_id: uuid.UUID | None = None,
    starts_at: datetime | None = None,
    duracion_min: int | None = None,
    motivo: str | None = None,
    permitir_sobrecupo: bool = False,
    ahora: datetime | None = None,
) -> Cita:
    """Edita o mueve una cita activa, revalidando las mismas reglas que al crearla.

    Actualización parcial: cada campo en None se deja como está. No cambia el paciente:
    para eso está `PUT /pacientes/{id}`. (Con esta semántica no se puede "vaciar" el
    motivo; es una limitación conocida y asumible para el MVP.)

    Reglas revalidadas sobre los valores efectivos: servicio y médico válidos, rejilla
    de minutos, disponibilidad (salvo sobrecupo, y solo si se mueve el hueco) y
    anti-solapamiento **excluyendo la propia cita**. La regla de "no en el pasado"
    solo se aplica si se mueve la hora.
    Hace flush (no commit): el commit lo hace el endpoint.
    """
    cita = _obtener_cita_activa(db, cita_id, CitaNoEditable)

    nuevo_medico_id = medico_id if medico_id is not None else cita.medico_id
    nuevo_servicio_id = servicio_id if servicio_id is not None else cita.servicio_id
    nuevo_starts_at = starts_at if starts_at is not None else cita.starts_at
    duracion_actual = int((cita.ends_at - cita.starts_at).total_seconds() // 60)
    nueva_duracion = duracion_min if duracion_min is not None else duracion_actual

    _validar_servicio_medico_y_rejilla(
        db, servicio_id=nuevo_servicio_id, medico_id=nuevo_medico_id, starts_at=nuevo_starts_at
    )

    if starts_at is not None:
        if ahora is None:
            ahora = ahora_centro()
        if nuevo_starts_at < ahora:
            raise CitaEnElPasado()

    nuevo_ends_at = calcular_ends_at(nuevo_starts_at, nueva_duracion)

    mismo_hueco = medico_id is None and starts_at is None and duracion_min is None
    _validar_hueco(
        db,
        medico_id=nuevo_medico_id,
        starts_at=nuevo_starts_at,
        ends_at=nuevo_ends_at,
        permitir_sobrecupo=permitir_sobrecupo or mismo_hueco,
        excluir_cita_id=cita.id,
    )

    cita.medico_id = nuevo_medico_id
    cita.servicio_id = nuevo_servicio_id
    cita.starts_at = nuevo_starts_at
    cita.ends_at = nuevo_ends_at
    if motivo is not None:
        cita.motivo = motivo
    db.flush()
    return cita
