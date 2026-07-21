"""Tests de las reglas de citas (R2, R3, R4) y del orquestador crear_cita."""

import uuid
from datetime import date, datetime, time

import pytest

from app.models import Cita, Disponibilidad, EstadoCita, Rol, Usuario
from app.schemas import CitaCreate, CitaUpdate
from app.services import citas as C

# Un lunes cualquiera, y su día en la convención del modelo (0=domingo).
LUNES_10 = datetime(2026, 7, 20, 10, 0)
DIA_LUNES = (LUNES_10.weekday() + 1) % 7
# Instante "actual" fijo para los tests: la medianoche de ese día, anterior a
# todas las citas de prueba. Se inyecta como `ahora` para que la regla de
# "no agendar en el pasado" sea determinista (no depende del reloj real).
ANTES = datetime(2026, 7, 20, 0, 0)


def _franja(db, medico, hora_inicio=time(8, 0), hora_fin=time(14, 0)):
    db.add(
        Disponibilidad(
            usuario_id=medico.id,
            dia_semana=DIA_LUNES,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        )
    )
    db.flush()


# --- Normalización de fecha con zona horaria (naive local) -------------------


def test_citacreate_convierte_fecha_con_zona_a_naive():
    # lo que manda el navegador con new Date().toISOString() lleva 'Z' (UTC)
    datos = CitaCreate(
        nombre_completo="Ana",
        edad=30,
        medico_id=uuid.uuid4(),
        servicio_id=uuid.uuid4(),
        starts_at="2026-07-20T10:00:00Z",
        duracion_min=45,
    )
    assert datos.starts_at.tzinfo is None                 # sin zona -> no rompe la comparación
    assert datos.starts_at == datetime(2026, 7, 20, 10, 0)  # se toma la hora tal cual (local)


def test_citaupdate_convierte_fecha_con_zona_a_naive():
    datos = CitaUpdate(starts_at="2026-07-20T11:30:00+00:00")
    assert datos.starts_at.tzinfo is None
    assert datos.starts_at == datetime(2026, 7, 20, 11, 30)


def test_citaupdate_sin_starts_at_no_falla():
    # el campo es opcional: si no viene, el validador no debe romper
    datos = CitaUpdate(motivo="control")
    assert datos.starts_at is None


# --- R2: duración ------------------------------------------------------------


def test_calcular_ends_at():
    fin = C.calcular_ends_at(datetime(2026, 7, 20, 10, 0), 45)
    assert fin == datetime(2026, 7, 20, 10, 45)  # 45 minutos de duración


# --- R0: rejilla de minutos (:00, :15, :30, :45) -----------------------------


def test_esta_alineado():
    # múltiplos de 15 (incluye 60=en punto y 90=:30) -> válidos
    assert C.esta_alineado(datetime(2026, 7, 20, 10, 0)) is True
    assert C.esta_alineado(datetime(2026, 7, 20, 10, 30)) is True
    assert C.esta_alineado(datetime(2026, 7, 20, 11, 45)) is True
    # fuera de rejilla o con segundos sueltos -> inválidos
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
            starts_at=datetime(2026, 7, 20, 10, 7),  # minuto :07 no está en la rejilla
            duracion_min=45,
            creado_por_id=admin.id,
        )


# --- R3: disponibilidad ------------------------------------------------------


def test_disponibilidad_dentro_y_fuera(db, medico):
    _franja(db, medico)  # lunes 08:00-14:00
    dentro = C.dentro_de_disponibilidad(
        db, medico.id, datetime(2026, 7, 20, 10, 0), datetime(2026, 7, 20, 10, 45)
    )
    fuera = C.dentro_de_disponibilidad(
        db, medico.id, datetime(2026, 7, 20, 7, 0), datetime(2026, 7, 20, 7, 45)
    )
    assert dentro is True
    assert fuera is False


# --- R4: anti-solapamiento ---------------------------------------------------


def test_solapamiento_y_citas_pegadas(db, medico, servicio, admin):
    pac = Usuario(nombre_completo=f"P {uuid.uuid4()}", edad=1, rol=Rol.PACIENTE)
    db.add(pac)
    db.flush()
    db.add(
        Cita(
            paciente_id=pac.id,
            medico_id=medico.id,
            servicio_id=servicio.id,
            starts_at=datetime(2026, 7, 20, 10, 0),
            ends_at=datetime(2026, 7, 20, 10, 45),
            estado=EstadoCita.SCHEDULED,
            creado_por_id=admin.id,
        )
    )
    db.flush()
    # se cruza -> True
    assert C.hay_solapamiento(
        db, medico.id, datetime(2026, 7, 20, 10, 30), datetime(2026, 7, 20, 11, 0)
    ) is True
    # pegada justo después -> False (se permite)
    assert C.hay_solapamiento(
        db, medico.id, datetime(2026, 7, 20, 10, 45), datetime(2026, 7, 20, 11, 30)
    ) is False


# --- Orquestador crear_cita --------------------------------------------------


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
    assert cita.estado == EstadoCita.SCHEDULED


def test_crear_cita_usa_la_duracion_elegida(db, medico, servicio, admin):
    # con una duración distinta de 45 se comprueba que el valor elegido SÍ se usa
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
    assert cita.ends_at == datetime(2026, 7, 20, 11, 30)  # 10:00 + 90 min


def test_crear_cita_fuera_de_disponibilidad(db, medico, servicio, admin):
    # sin franja -> cualquier hora está fuera
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
    # admin no tiene rol MEDICO
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


def test_crear_cita_en_el_pasado(db, medico, servicio, admin):
    _franja(db, medico)
    # 'ahora' posterior al inicio -> la cita queda en el pasado
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
            ahora=datetime(2026, 7, 20, 11, 0),  # ya pasaron las 10:00
        )


def test_crear_cita_medico_inactivo(db, servicio, admin):
    # médico con rol correcto pero dado de baja (activo=False) -> no agendable
    inactivo = Usuario(
        nombre_completo=f"Dr. Baja {uuid.uuid4()}",
        rol=Rol.MEDICO,
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


# --- Listar agenda -----------------------------------------------------------


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


FECHA_LUNES = LUNES_10.date()  # date(2026, 7, 20)


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
    assert [c.starts_at.hour for c in del_dia] == [9, 11]  # ordenadas por inicio
    assert otro_dia == []


def test_listar_excluye_canceladas_por_defecto(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)
    vigentes = C.listar_citas(db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=medico.id)
    con_canceladas = C.listar_citas(
        db, desde=FECHA_LUNES, hasta=FECHA_LUNES, medico_id=medico.id, incluir_canceladas=True
    )
    assert vigentes == []          # la cancelada no aparece por defecto
    assert len(con_canceladas) == 1  # con el flag, sí


# --- Cancelar cita -----------------------------------------------------------


def test_cancelar_cita_libera_cupo(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)
    assert cita.estado == EstadoCita.CANCELLED
    # el hueco queda libre: agendar otra a la misma hora ya no solapa
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
    assert otra.estado == EstadoCita.SCHEDULED


def test_cancelar_cita_inexistente(db):
    with pytest.raises(C.CitaNoEncontrada):
        C.cancelar_cita(db, uuid.uuid4())


def test_cancelar_cita_ya_cancelada(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)
    with pytest.raises(C.CitaNoCancelable):
        C.cancelar_cita(db, cita.id)  # segunda vez -> no cancelable


# --- Asistencia (atendida / no-show) -----------------------------------------


def test_marcar_asistencia_atendida(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.marcar_asistencia(db, cita.id, EstadoCita.COMPLETED)
    assert cita.estado == EstadoCita.COMPLETED


def test_marcar_asistencia_no_show(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.marcar_asistencia(db, cita.id, EstadoCita.NO_SHOW)
    assert cita.estado == EstadoCita.NO_SHOW


def test_marcar_asistencia_inexistente(db):
    with pytest.raises(C.CitaNoEncontrada):
        C.marcar_asistencia(db, uuid.uuid4(), EstadoCita.COMPLETED)


def test_marcar_asistencia_cita_no_activa(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)  # cancelada -> ya no está activa
    with pytest.raises(C.CitaNoActiva):
        C.marcar_asistencia(db, cita.id, EstadoCita.COMPLETED)


# --- Editar / mover cita -----------------------------------------------------


def test_editar_mueve_la_hora(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)  # 10:00-10:45
    C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 11, 0), ahora=ANTES)
    assert cita.starts_at == datetime(2026, 7, 20, 11, 0)
    assert cita.ends_at == datetime(2026, 7, 20, 11, 45)  # conserva los 45 min


def test_editar_cambia_la_duracion(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)  # 10:00-10:45
    C.editar_cita(db, cita.id, duracion_min=90, ahora=ANTES)
    assert cita.ends_at == datetime(2026, 7, 20, 11, 30)  # 10:00 + 90 min


def test_editar_no_solapa_consigo_misma(db, medico, servicio, admin):
    # mover dentro de su propio tramo no debe chocar con ella misma
    cita = _cita(db, medico, servicio, admin, LUNES_10)  # 10:00-10:45
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
        starts_at=datetime(2026, 7, 20, 9, 0),  # 09:00-09:45
        duracion_min=45,
        creado_por_id=admin.id,
        ahora=ANTES,
    )
    cita = _cita(db, medico, servicio, admin, LUNES_10)  # 10:00-10:45
    # mover 'cita' encima de 'otra' -> choca
    with pytest.raises(C.Solapamiento):
        C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 9, 30), ahora=ANTES)
    assert otra.id != cita.id


def test_editar_cita_inexistente(db):
    with pytest.raises(C.CitaNoEncontrada):
        C.editar_cita(db, uuid.uuid4(), motivo="x")


def test_editar_cita_no_activa(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.cancelar_cita(db, cita.id)  # cancelada -> ya no es editable
    with pytest.raises(C.CitaNoEditable):
        C.editar_cita(db, cita.id, motivo="x")


def test_editar_fuera_de_disponibilidad(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)  # franja 08:00-14:00
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
            ahora=datetime(2026, 7, 20, 12, 0),  # ya pasaron las 11:00
        )


def test_editar_sin_mover_hora_no_valida_pasado(db, medico, servicio, admin):
    # cambiar solo el motivo no dispara la regla del pasado (no se mueve la hora)
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    C.editar_cita(db, cita.id, motivo="control", ahora=datetime(2026, 7, 20, 23, 0))
    assert cita.motivo == "control"


def test_editar_motivo_none_conserva_el_actual(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    cita.motivo = "revisión"
    db.flush()
    C.editar_cita(db, cita.id, starts_at=datetime(2026, 7, 20, 11, 0), ahora=ANTES)
    assert cita.motivo == "revisión"  # no se envió motivo -> se conserva


# --- Historial de citas de un paciente ---------------------------------------


def test_listar_citas_de_paciente_historial(db, medico, servicio, admin):
    cita = _cita(db, medico, servicio, admin, LUNES_10)
    historial = C.listar_citas_de_paciente(db, cita.paciente_id)
    assert [c.id for c in historial] == [cita.id]  # solo su cita, y es la suya
