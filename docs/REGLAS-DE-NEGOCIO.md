# ERP Diagnóstico — Reglas de Negocio

> **Referencia canónica** de las reglas de negocio del sistema y de **cómo se implementan**.
> Toda la validación vive en la **capa de servicio** del backend (`app/services/`), en Python,
> **antes de guardar** en la base de datos, para dar mensajes de error claros y poder probarla aislada.
> Estado a **22/07/2026** (MVP). Complementa [`MODELO-DATOS.md`](MODELO-DATOS.md) y [`ARQUITECTURA.md`](ARQUITECTURA.md).

## Resumen

| # | Regla | Implementación | Estado |
|---|-------|----------------|:------:|
| R0 | El inicio cae en la rejilla de 15 min (:00/:15/:30/:45) | `is_aligned()` · `app/services/appointments.py` | ✅ |
| R0.b | No se puede agendar en el pasado | check en `create_appointment()` (`AppointmentInThePast`) | ✅ |
| R0.c | El médico debe existir, tener rol MEDICO y estar activo | check en `create_appointment()` (`MedicoNoEncontrado`) | ✅ |
| R1 | Upsert de paciente al agendar | `find_or_create_patient()` · `app/services/patients.py` | ✅ |
| R2 | La duración la elige recepción al agendar | `calculate_ends_at()` · `app/services/appointments.py` | ✅ |
| R3 | La cita cae dentro de la disponibilidad del médico | `within_availability()` · `app/services/appointments.py` | ✅ |
| R4 | Cero solapamientos por médico | `has_overlap()` · `app/services/appointments.py` | ✅ |
| R5 | Cancelar libera el hueco | filtro de estados en R4 | ✅ (regla) |
| R6 | Marcar asistencia (atendida/no-show) solo sobre citas activas | `mark_attendance()` · `app/services/appointments.py` | ✅ |
| R7 | Las franjas de un médico no se solapan entre sí | `has_overlapping_slot()` · `app/services/availability.py` | ✅ |
| R8 | Editar o borrar una franja no puede dejar citas fuera de horario | `update_availability()` / `delete_availability()` · `app/services/availability.py` | ✅ |
| — | Orquestación de todas al crear la cita | `create_appointment()` + `POST /citas` | ✅ |

---

## R0 · El inicio cae en la rejilla de 15 minutos

**Regla.** Una cita solo puede empezar en un minuto de rejilla: **:00, :15, :30 o :45** (múltiplos de 15, sin segundos sueltos). Evita horas irregulares (10:07) y mantiene la agenda ordenada.

**Implementación.** `is_aligned(starts_at)` en `app/services/appointments.py`; si falla, `create_appointment` lanza `TimeNotAligned` → **400**.

---

## R0.b · No se puede agendar en el pasado

**Regla.** El inicio de la cita debe ser **futuro**; no se agenda una cita cuya hora de inicio ya pasó.

**Implementación.** Comparación con la hora actual en `create_appointment` (reloj inyectable para poder testear); si el inicio ya pasó, lanza `AppointmentInThePast` → **400**.

---

## R0.c · El médico debe estar activo

**Regla.** Solo se agenda con un usuario que exista, tenga **rol MEDICO** y esté **activo** (un médico dado de baja no es agendable).

**Implementación.** Validación en `create_appointment`; si no cumple, lanza `MedicoNoEncontrado` → **404**.

---

## R1 · Upsert de paciente al agendar

**Regla.** Al crear una cita no se elige el paciente de una lista: recepción teclea sus datos y el
sistema **detecta** si ya existe o lo **crea**, para no duplicar.

- Se identifica por **`nombre_completo` + `edad`** (lo que pide recepción; la cédula es opcional y se añade después).
- **1 coincidencia** → se reutiliza. **0 coincidencias** → se crea con `rol = PACIENTE`. **Varias** → recepción **elige** (se señala con la excepción `PacientesAmbiguos`).

**Implementación.** `find_or_create_patient(db, nombre_completo, edad)` en `app/services/patients.py`.
Hace `flush` (no `commit`): el paciente nuevo obtiene su `id` pero se guarda dentro de la transacción de la cita.

---

## R2 · La duración la elige recepción al agendar

**Regla.** Al agendar, **recepción elige la duración** de una lista fija: **{15, 30, 45, 60, 90} minutos**. El servicio ya **no** marca la duración.

$$ \text{ends\_at} = \text{starts\_at} + \text{duracion\_min} $$

Ej.: cita a las 10:00 con **45 min** elegidos → termina a las 10:45.

**Implementación.** `calculate_ends_at(starts_at, duracion_min)` en `app/services/appointments.py`. El valor se valida en el schema `AppointmentCreate` (`Literal[15,30,45,60,90]` → 422 si no es válido).

---

## R3 · La cita cae dentro de la disponibilidad del médico

**Regla.** Cada médico define franjas semanales (`disponibilidad`). La cita debe caer **entera**
(inicio **y** fin) dentro de **una** franja de ese médico ese día de la semana.

- El día se convierte a la convención del modelo (**0 = domingo**) con `(fecha.weekday() + 1) % 7`.
- Condición: `franja.hora_inicio ≤ cita.inicio` **y** `cita.fin ≤ franja.hora_fin`.
- **Sobrecupo:** si la cita cae fuera, recepción puede **forzar un cupo extra** (override) de mutuo acuerdo. *(Lo aplica `create_appointment` con `permitir_sobrecupo`.)*

**Implementación.** `within_availability(db, medico_id, starts_at, ends_at)` en `app/services/appointments.py`.

---

## R4 · Cero solapamientos por médico *(regla estrella)*

**Regla.** Un médico **no** puede tener dos citas **activas** que se crucen en el tiempo. Esto **siempre se bloquea** (incluso con sobrecupo).

- Dos citas se cruzan si: `nueva.inicio < existente.fin` **y** `nueva.fin > existente.inicio`.
- Solo cuentan las **activas** (`SCHEDULED` / `CONFIRMED`).
- Citas **pegadas** (una acaba justo cuando empieza la otra) **no** se solapan → se permiten.
- Es **por médico** (dos médicos pueden atender a la misma hora).
**Implementación.** `has_overlap(db, medico_id, starts_at, ends_at)`
en `app/services/appointments.py` (consulta `EXISTS` sobre las citas activas del médico).

---

## R5 · Cancelar libera el hueco

**Regla.** Al pasar una cita a `CANCELLED`, sale de los estados activos y su hueco **se reutiliza**.

**Implementación.** No necesita código propio: R4 solo mira las citas `SCHEDULED`/`CONFIRMED`, así que
una cancelada deja de contar automáticamente. *(El cambio de estado lo hace `cancel_appointment` / `POST /citas/{id}/cancelar`.)*

---

## R6 · Marcar asistencia (atendida / no-show)

**Regla.** Una cita **activa** (`SCHEDULED`/`CONFIRMED`) se cierra como **atendida** (`COMPLETED`) o **no-show** (`NO_SHOW`); no se puede marcar sobre una cita ya cerrada o cancelada. Lo hacen **recepción y admin** (el médico solo consulta su agenda, no marca asistencia).

**Implementación.** `mark_attendance(db, cita_id, estado)` en `app/services/appointments.py` (reutiliza `_get_active_appointment`); si la cita no está activa lanza `AppointmentNotActive` → **409**. Endpoint `POST /citas/{id}/asistencia` con `estado ∈ {COMPLETED, NO_SHOW}`.

---

## R7 · Las franjas de un médico no se solapan entre sí

**Regla.** Un médico no puede tener dos franjas de disponibilidad **cruzadas el mismo día**. "Lunes 08:00–12:00" y "Lunes 10:00–14:00" no pueden coexistir; "Lunes 08:00–12:00" y "Lunes 12:00–16:00" sí, porque son **contiguas, no solapadas**.

**Implementación.** `has_overlapping_slot()` en `app/services/availability.py`, con la misma regla de intersección que R4 (`inicio_nuevo < fin_existente` **y** `fin_nuevo > inicio_existente`, con `<` estrictos). Se aplica al crear y al editar; al editar se excluye la propia franja para que no choque consigo misma. Lanza `OverlappingSlot` → **409**.

**Por qué importa más de lo que parece.** Al garantizar que no hay solapes, **cada cita queda cubierta por una única franja**. Eso es lo que hace que R8 pueda comprobarse de forma exacta y no aproximada.

---

## R8 · Editar o borrar una franja no puede dejar citas fuera de horario

**Regla.** Si se **elimina** una franja, o se **reduce** de forma que alguna cita agendada deje de caber dentro, la operación se **rechaza**. Recepción debe mover o cancelar esas citas primero.

**Por qué.** La disponibilidad solo se comprueba **al crear** la cita (R3). Una cita ya agendada no se entera de que su franja cambió, así que sin esta regla quedarían citas activas fuera del horario del médico sin que nadie avisara.

**Qué cuenta como problema.** Solo las citas **activas** (`SCHEDULED`/`CONFIRMED`) y **futuras**. Una cita cancelada o ya pasada no bloquea nada.

**Implementación.** `update_availability()` y `delete_availability()` en `app/services/availability.py` usan `_covered_appointments()`, que localiza las citas que esa franja está sosteniendo; si alguna quedaría fuera del nuevo rango, lanza `StrandedAppointments` → **409**, con el número de citas afectadas en el mensaje para que la interfaz pueda decirlo.

**Ampliar una franja siempre se permite**: si el horario crece, ninguna cita puede quedarse fuera.

---

## Orden al crear una cita (orquestación)

El servicio `create_appointment` llama a las reglas **en este orden** y guarda todo con **un solo `commit`** (o nada, si algo falla):

1. **Validaciones de entrada:** el servicio existe; el médico existe, tiene rol MEDICO y está activo (**R0.c**); el inicio cae en la rejilla (**R0**) y **no** está en el pasado (**R0.b**).
2. **R1** — upsert del paciente.
3. **R2** — calcular `ends_at` con la duración elegida.
4. **R3** — validar disponibilidad (si falla → error, salvo sobrecupo).
5. **R4** — validar anti-solapamiento (si falla → error **siempre**).
6. Crear la cita y **`commit`**.

---

## Fuera del MVP (fase 2)

Reglas que evolucionarán en fase 2 (anti-solapamiento por recurso/sala, constraint `gist` en BD, duración por médico, Holter con retiro): ver **[`MEJORAS-Y-PROXIMOS-PASOS.md`](MEJORAS-Y-PROXIMOS-PASOS.md)**.
