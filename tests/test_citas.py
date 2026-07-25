"""Tests de las reglas de citas (R2, R3, R4) y del orquestador crear_cita."""

import uuid
from datetime import date, datetime, time, timezone

import pytest
from pydantic import ValidationError

from app.enums import AppointmentStatus, Role
from app.models import Appointment, Availability, User
from app.schemas import CitaCreate, CitaUpdate
from app.services import citas as C

LUNES_10 = datetime(2026, 7, 20, 10, 0)
DIA_LUNES = (LUNES_10.weekday() + 1) % 7
ANTES = datetime(2026, 7, 20, 0, 0)


def _franja(db, medico, hora_inicio=time(8, 0), hora_fin=time(14, 0)):
    db.add(
        Availability(
            usuario_id=medico.id,
            dia_semana=DIA_LUNES,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        )
    )
    db.flush()


def test_citacreate_rechaza_fecha_con_zona():
    with pytest.raises(ValidationError):
        CitaCreate(
            nombre_completo="Ana",
            edad=30,
            medico_id=uuid.uuid4(),
            servicio_id=uuid.uuid4(),
            starts_at="2026-07-20T10:00:00Z",
            duracion_min=45,
        )


def test_citacreate_acepta_fecha_naive():
    datos = CitaCreate(
        nombre_completo="Ana",
        edad=30,
        medico_id=uuid.uuid4(),
        servicio_id=uuid.uuid4(),
        starts_at="2026-07-20T10:00:00",
        duracion_min=45,
    )
    assert datos.starts_at == datetime(2026, 7, 20, 10, 0)


def test_citaupdate_rechaza_fecha_con_zona():
    with pytest.raises(ValidationError):
        CitaUpdate(starts_at="2026-07-20T11:30:00+00:00")


def test_citaupdate_sin_starts_at_no_falla():
    datos = CitaUpdate(motivo="control")
    assert datos.starts_at is None


def test_ahora_centro_es_naive_y_utc_menos_4():
    got = C.ahora_centro()
    assert got.tzinfo is None
    utc = datetime.now(timezone.utc).replace(tzinfo=None)
    horas_detras = (utc - got).total_seconds() / 3600
    assert 3.5 < horas_detras < 4.5


def test_calcular_ends_at():
    fin = C.calcular_ends_at(datetime(2026, 7, 20, 10, 0), 45)
    assert fin == datetime(2026, 7, 20, 10, 45)


def test_esta_alineado():
    assert C.esta_alineado(datetime(2026, 7, 20, 10, 0)) is True
    assert C.esta_alineado(datetime(2026, 7, 20, 10, 30)) is True
    assert C.esta_alineado(datetime(2026, 7, 20, 11, 45)) is True
    assert C.esta_alineado(datetime(2026, 7, 20, 10, 7)) is False
    assert C.esta_alineado(datetime(2026, 7, 20, 10, 15, 30)) is False


def test_crear_cita_horario_no_alineado(db, medico, servicio, admin):
    _franja(db, medico)
    with pytest.raises(C.HorarioNoAlineado):
        C.crear_cita(
            db,
            nombre_completo=f"X {uuid.uuid4()}",
            edad=1,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=datetime(2026, 7, 20, 10, 7),
            duracion_min=45,
            creado_por_id=admin.id,
        )


def test_disponibilidad_dentro_y_fuera(db, medico):
    _franja(db, medico)
    dentro = C.dentro_de_disponibilidad(
        db, medico.id, datetime(2026, 7, 20, 10, 0), datetime(2026, 7, 20, 10, 45)
    )
    fuera = C.dentro_de_disponibilidad(
        db, medico.id, datetime(2026, 7, 20, 7, 0), datetime(2026, 7, 20, 7, 45)
    )
    assert dentro is True
    assert fuera is False


def test_solapamiento_y_citas_pegadas(db, medico, servicio, admin):
    pac = User(nombre_completo=f"P {uuid.uuid4()}", edad=1, rol=Role.PACIENTE)
    db.add(pac)
    db.flush()
    db.add(
        Appointment(
            paciente_id=pac.id,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=datetime(2026, 7, 20, 10, 0),
            ends_at=datetime(2026, 7, 20, 10, 45),
            estado=AppointmentStatus.SCHEDULED,
            creado_por_id=admin.id,
        )
    )
    db.flush()
    assert C.hay_solapamiento(
        db, medico.id, datetime(2026, 7, 20, 10, 30), datetime(2026, 7, 20, 11, 0)
    ) is True
    assert C.hay_solapamiento(
        db, medico.id, datetime(2026, 7, 20, 10, 45), datetime(2026, 7, 20, 11, 30)
    ) is False


def test_crear_cita_feliz(db, medico, servicio, admin):
    _franja(db, medico)
    cita = C.crear_cita(
        db,
        nombre_completo=f"Ana {uuid.uuid4()}",
        edad=33,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    assert cita.ends_at == datetime(2026, 7, 20, 10, 45)
    assert cita.estado == AppointmentStatus.SCHEDULED


def test_crear_cita_con_paciente_id_resuelve_ambiguedad(db, medico, servicio, admin):
    _franja(db, medico)
    p1 = User(nombre_completo="Ambiguo", edad=40, rol=Role.PACIENTE)
    p2 = User(nombre_completo="Ambiguo", edad=40, rol=Role.PACIENTE)
    db.add_all([p1, p2])
    db.flush()
    cita = C.crear_cita(
        db,
        nombre_completo="Ambiguo",
        edad=40,
        paciente_id=p1.id,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    assert cita.paciente_id == p1.id


def test_crear_cita_usa_la_duracion_elegida(db, medico, servicio, admin):
    _franja(db, medico)
    cita = C.crear_cita(
        db,
        nombre_completo=f"Dur {uuid.uuid4()}",
        edad=1,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=LUNES_10,
        duracion_min=90,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    assert cita.ends_at == datetime(2026, 7, 20, 11, 30)


def test_crear_cita_fuera_de_disponibilidad(db, medico, servicio, admin):
    with pytest.raises(C.FueraDeDisponibilidad):
        C.crear_cita(
            db,
            nombre_completo=f"X {uuid.uuid4()}",
            edad=1,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
            ahora=ANTES,
        )


def test_crear_cita_bloquea_solapamiento(db, medico, servicio, admin):
    _franja(db, medico)
    C.crear_cita(
        db,
        nombre_completo=f"A {uuid.uuid4()}",
        edad=1,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    with pytest.raises(C.Solapamiento):
        C.crear_cita(
            db,
            nombre_completo=f"B {uuid.uuid4()}",
            edad=2,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=datetime(2026, 7, 20, 10, 30),
            duracion_min=45,
            creado_por_id=admin.id,
            ahora=ANTES,
        )


def test_crear_cita_medico_invalido(db, servicio, admin):
    with pytest.raises(C.MedicoNoEncontrado):
        C.crear_cita(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=admin.id,
            servicio_id=servicio.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
        )


def test_crear_cita_servicio_invalido(db, medico, admin):
    with pytest.raises(C.ServicioNoEncontrado):
        C.crear_cita(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=medico.id,
            servicio_id=uuid.uuid4(),
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
        )


def test_crear_cita_servicio_inactivo(db, medico, servicio, admin):
    servicio.activo = False
    db.flush()
    with pytest.raises(C.ServicioNoEncontrado):
        C.crear_cita(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
        )


def test_editar_cita_sobrecupo_solo_motivo(db, medico, servicio, admin):
    cita = C.crear_cita(
        db,
        nombre_completo=f"X {uuid.uuid4()}",
        edad=1,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        permitir_sobrecupo=True,
        ahora=ANTES,
    )
    actualizada = C.editar_cita(db, cita.id, motivo="control")
    assert actualizada.motivo == "control"


def test_crear_cita_en_el_pasado(db, medico, servicio, admin):
    _franja(db, medico)
    with pytest.raises(C.CitaEnElPasado):
        C.crear_cita(
            db,
            nombre_completo=f"X {uuid.uuid4()}",
            edad=1,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
            ahora=datetime(2026, 7, 20, 11, 0),
        )


def test_crear_cita_medico_inactivo(db, servicio, admin):
    inactivo = User(
        nombre_completo=f"Dr. Baja {uuid.uuid4()}",
        rol=Role.MEDICO,
        email=f"baja-{uuid.uuid4()}@test.local",
        activo=False,
    )
    db.add(inactivo)
    db.flush()
    with pytest.raises(C.MedicoNoEncontrado):
        C.crear_cita(
            db,
            nombre_completo="X",
            edad=1,
            medico_id=inactivo.id,
            servicio_id=servicio.id,
            starts_at=LUNES_10,
            duracion_min=45,
            creado_por_id=admin.id,
            ahora=ANTES,
        )


def _cita(db, medico, servicio, admin, starts_at):
    """Crea y devuelve una cita ya agendada (con franja disponible)."""
    _franja(db, medico)
    return C.crear_cita(
        db,
        nombre_completo=f"P {uuid.uuid4()}",
        edad=1,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=starts_at,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )


FECHA_LUNES = LUNES_10.date()


def test_listar_filtra_por_medico(db, medico, servicio, admin):
    _cita(db, medico, servicio, admin, LUNES_10)
    del_medico = C.listar_citas(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=medico.id)
    de_otro = C.listar_citas(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=uuid.uuid4())
    assert len(del_medico) == 1
    assert de_otro == []


def test_listar_por_rango_y_ordena(db, medico, servicio, admin):
    _cita(db, medico, servicio, admin, datetime(2026, 7, 20, 11, 0))
    _cita(db, medico, servicio, admin, datetime(2026, 7, 20, 9, 0))
    del_dia = C.listar_citas(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=medico.id)
    otro_dia = C.listar_citas(
        db, desde=date(2026, 7, 21), hasta=date(2026, 7, 21), medico_id=medico.id
    )
    assert [c.starts_at.hour for c in del_dia] == [9, 11]
    assert otro_dia == []


def test_listar_excluye_canceladas_por_defecto(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)
    vigentes = C.listar_citas(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=medico.id)
    con_canceladas = C.listar_citas(
        db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=medico.id, incluir_canceladas=True
    )
    assert vigentes == []
    assert len(con_canceladas) == 1


def test_cancelar_cita_libera_cupo(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)
    assert cita.estado == AppointmentStatus.CANCELLED
    otra = C.crear_cita(
        db,
        nombre_completo=f"Q {uuid.uuid4()}",
        edad=2,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=LUNES_10,
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    assert otra.estado == AppointmentStatus.SCHEDULED


def test_cancelar_cita_inexistente(db):
    with pytest.raises(C.CitaNoEncontrada):
        C.cancelar_cita(db, uuid.uuid4())


def test_cancelar_cita_ya_cancelada(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)
    with pytest.raises(C.CitaNoCancelable):
        C.cancelar_cita(db, cita.id)


def test_marcar_asistencia_atendida(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.marcar_asistencia(db, cita.id, AppointmentStatus.COMPLETED)
    assert cita.estado == AppointmentStatus.COMPLETED


def test_marcar_asistencia_no_show(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.marcar_asistencia(db, cita.id, AppointmentStatus.NO_SHOW)
    assert cita.estado == AppointmentStatus.NO_SHOW


def test_marcar_asistencia_inexistente(db):
    with pytest.raises(C.CitaNoEncontrada):
        C.marcar_asistencia(db, uuid.uuid4(), AppointmentStatus.COMPLETED)


def test_marcar_asistencia_cita_no_activa(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)
    with pytest.raises(C.CitaNoActiva):
        C.marcar_asistencia(db, cita.id, AppointmentStatus.COMPLETED)


def test_editar_mueve_la_hora(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 11, 0), ahora=ANTES)
    assert cita.starts_at == datetime(2026, 7, 20, 11, 0)
    assert cita.ends_at == datetime(2026, 7, 20, 11, 45)


def test_editar_cambia_la_duracion(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.editar_cita(db, cita.id, duracion_min=90, ahora=ANTES)
    assert cita.ends_at == datetime(2026, 7, 20, 11, 30)


def test_editar_no_solapa_consigo_misma(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 10, 15), ahora=ANTES)
    assert cita.starts_at == datetime(2026, 7, 20, 10, 15)


def test_editar_bloquea_solapamiento_con_otra(db, medico, servicio, admin):
    _franja(db, medico)
    otra = C.crear_cita(
        db,
        nombre_completo=f"Otra {uuid.uuid4()}",
        edad=1,
        medico_id=medico.id,
        servicio_id=servicio.id,
        starts_at=datetime(2026, 7, 20, 9, 0),
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    with pytest.raises(C.Solapamiento):
        C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 9, 30), ahora=ANTES)
    assert otra.id != cita.id


def test_editar_cita_inexistente(db):
    with pytest.raises(C.CitaNoEncontrada):
        C.editar_cita(db, uuid.uuid4(), motivo="x")


def test_editar_cita_no_activa(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)
    with pytest.raises(C.CitaNoEditable):
        C.editar_cita(db, cita.id, motivo="x")


def test_editar_fuera_de_disponibilidad(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    with pytest.raises(C.FueraDeDisponibilidad):
        C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 7, 0), ahora=ANTES)


def test_editar_horario_no_alineado(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    with pytest.raises(C.HorarioNoAlineado):
        C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 11, 7), ahora=ANTES)


def test_editar_al_pasado(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    with pytest.raises(C.CitaEnElPasado):
        C.editar_cita(
            db,
            cita.id,
            starts_at=datetime(2026, 7, 20, 11, 0),
            ahora=datetime(2026, 7, 20, 12, 0),
        )


def test_editar_sin_mover_hora_no_valida_pasado(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.editar_cita(db, cita.id, motivo="control", ahora=datetime(2026, 7, 20, 23, 0))
    assert cita.motivo == "control"


def test_editar_motivo_none_conserva_el_actual(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    cita.motivo = "revisión"
    db.flush()
    C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 11, 0), ahora=ANTES)
    assert cita.motivo == "revisión"


def test_listar_citas_de_paciente_historial(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    historial = C.listar_citas_de_paciente(db, cita.paciente_id)
    assert [c.id for c in historial] == [cita.id]
