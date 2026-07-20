# ERP Diagnóstico — Reglas de Negocio

> **Referencia canónica** de las reglas de negocio del sistema y de **cómo se implementan**.
> Toda la validación vive en la **capa de servicio** del backend (`app/services/`), en Python,
> **antes de guardar** en la base de datos, para dar mensajes de error claros y poder probarla aislada.
> Estado a **15/07/2026** (MVP). Complementa [`MODELO-DATOS.md`](MODELO-DATOS.md) y [`ARQUITECTURA.md`](ARQUITECTURA.md).

## Resumen

| # | Regla | Implementación | Estado |
|---|-------|----------------|:------:|
| R0 | El inicio cae en la rejilla de 15 min (:00/:15/:30/:45) | `esta_alineado()` · `app/services/citas.py` | ✅ |
| R0.b | No se puede agendar en el pasado | check en `crear_cita()` (`CitaEnElPasado`) | ✅ |
| R0.c | El médico debe existir, tener rol MEDICO y estar activo | check en `crear_cita()` (`MedicoNoEncontrado`) | ✅ |
| R1 | Upsert de paciente al agendar | `buscar_o_crear_paciente()` · `app/services/pacientes.py` | ✅ |
| R2 | La duración la elige recepción al agendar | `calcular_ends_at()` · `app/services/citas.py` | ✅ |
| R3 | La cita cae dentro de la disponibilidad del médico | `dentro_de_disponibilidad()` · `app/services/citas.py` | ✅ |
| R4 | Cero solapamientos por médico | `hay_solapamiento()` · `app/services/citas.py` | ✅ |
| R5 | Cancelar libera el hueco | filtro de estados en R4 | ✅ (regla) |
| — | Orquestación de todas al crear la cita | `crear_cita()` + `POST /citas` | ✅ |

---

## R0 · El inicio cae en la rejilla de 15 minutos

**Regla.** Una cita solo puede empezar en un minuto de rejilla: **:00, :15, :30 o :45** (múltiplos de 15, sin segundos sueltos). Evita horas irregulares (10:07) y mantiene la agenda ordenada.

**Implementación.** `esta_alineado(starts_at)` en `app/services/citas.py`; si falla, `crear_cita` lanza `HorarioNoAlineado` → **400**.

---

## R0.b · No se puede agendar en el pasado

**Regla.** El inicio de la cita debe ser **futuro**; no se agenda una cita cuya hora de inicio ya pasó.

**Implementación.** Comparación con la hora actual en `crear_cita` (reloj inyectable para poder testear); si el inicio ya pasó, lanza `CitaEnElPasado` → **400**.

---

## R0.c · El médico debe estar activo

**Regla.** Solo se agenda con un usuario que exista, tenga **rol MEDICO** y esté **activo** (un médico dado de baja no es agendable).

**Implementación.** Validación en `crear_cita`; si no cumple, lanza `MedicoNoEncontrado` → **404**.

---

## R1 · Upsert de paciente al agendar

**Regla.** Al crear una cita no se elige el paciente de una lista: recepción teclea sus datos y el
sistema **detecta** si ya existe o lo **crea**, para no duplicar.

- Se identifica por **`nombre_completo` + `edad`** (lo que pide recepción; la cédula es opcional y se añade después).
- **1 coincidencia** → se reutiliza. **0 coincidencias** → se crea con `rol = PACIENTE`. **Varias** → recepción **elige** (se señala con la excepción `PacientesAmbiguos`).

**Implementación.** `buscar_o_crear_paciente(db, nombre_completo, edad)` en `app/services/pacientes.py`.
Hace `flush` (no `commit`): el paciente nuevo obtiene su `id` pero se guarda dentro de la transacción de la cita.

---

## R2 · La duración la elige recepción al agendar

**Regla.** Al agendar, **recepción elige la duración** de una lista fija: **{15, 30, 45, 60, 90} minutos**. El servicio ya **no** marca la duración.

$$ \text{ends\_at} = \text{starts\_at} + \text{duracion\_min} $$

Ej.: cita a las 10:00 con **45 min** elegidos → termina a las 10:45.

**Implementación.** `calcular_ends_at(starts_at, duracion_min)` en `app/services/citas.py`. El valor se valida en el schema `CitaCreate` (`Literal[15,30,45,60,90]` → 422 si no es válido).

---

## R3 · La cita cae dentro de la disponibilidad del médico

**Regla.** Cada médico define franjas semanales (`disponibilidad`). La cita debe caer **entera**
(inicio **y** fin) dentro de **una** franja de ese médico ese día de la semana.

- El día se convierte a la convención del modelo (**0 = domingo**) con `(fecha.weekday() + 1) % 7`.
- Condición: `franja.hora_inicio ≤ cita.inicio` **y** `cita.fin ≤ franja.hora_fin`.
- **Sobrecupo:** si la cita cae fuera, recepción puede **forzar un cupo extra** (override) de mutuo acuerdo. *(Lo aplica `crear_cita` con `permitir_sobrecupo`.)*

**Implementación.** `dentro_de_disponibilidad(db, medico_id, starts_at, ends_at)` en `app/services/citas.py`.

---

## R4 · Cero solapamientos por médico *(regla estrella)*

**Regla.** Un médico **no** puede tener dos citas **activas** que se crucen en el tiempo. Esto **siempre se bloquea** (incluso con sobrecupo).

- Dos citas se cruzan si: `nueva.inicio < existente.fin` **y** `nueva.fin > existente.inicio`.
- Solo cuentan las **activas** (`SCHEDULED` / `CONFIRMED`).
- Citas **pegadas** (una acaba justo cuando empieza la otra) **no** se solapan → se permiten.
- Es **por médico** (dos médicos pueden atender a la misma hora).
**Implementación.** `hay_solapamiento(db, medico_id, starts_at, ends_at)`
en `app/services/citas.py` (consulta `EXISTS` sobre las citas activas del médico).

---

## R5 · Cancelar libera el hueco

**Regla.** Al pasar una cita a `CANCELLED`, sale de los estados activos y su hueco **se reutiliza**.

**Implementación.** No necesita código propio: R4 solo mira las citas `SCHEDULED`/`CONFIRMED`, así que
una cancelada deja de contar automáticamente. *(El cambio de estado lo hace `cancelar_cita` / `POST /citas/{id}/cancelar`.)*

---

## Orden al crear una cita (orquestación)

El servicio `crear_cita` llama a las reglas **en este orden** y guarda todo con **un solo `commit`** (o nada, si algo falla):

1. **Validaciones de entrada:** el servicio existe; el médico existe, tiene rol MEDICO y está activo (**R0.c**); el inicio cae en la rejilla (**R0**) y **no** está en el pasado (**R0.b**).
2. **R1** — upsert del paciente.
3. **R2** — calcular `ends_at` con la duración elegida.
4. **R3** — validar disponibilidad (si falla → error, salvo sobrecupo).
5. **R4** — validar anti-solapamiento (si falla → error **siempre**).
6. Crear la cita y **`commit`**.

---

## Fuera del MVP (fase 2)

- **Anti-solapamiento por recurso/sala** (equipos únicos: ecógrafo, etc.) — hoy solo por médico.
- **Constraint `gist` en la base de datos** como segunda barrera al solapamiento.
- **Duración por médico** (`medico_servicio`) automática — hoy la duración la elige recepción a mano.
- **Holter/MAPA con retiro** enlazado a la colocación.
