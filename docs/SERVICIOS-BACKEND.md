# ERP Diagnóstico — Servicios de Backend

> La **capa de servicios** (`app/services/`) concentra toda la **lógica de negocio**.
> Los routers (`app/controller/`) solo validan el HTTP, delegan en el servicio y traducen
> las excepciones de dominio a códigos HTTP. Así la lógica se puede **probar sin levantar la API**.

## Principios comunes a todos los servicios

- **Sin dependencia de FastAPI:** reciben una `Session` de SQLAlchemy y datos simples; no conocen `Request` ni `Response`.
- **`flush`, no `commit`:** los servicios hacen `db.flush()` (asignan ids, validan constraints) pero **no confirman**. El `commit` lo hace el endpoint, para que toda la petición sea una única transacción.
- **Excepciones de dominio:** cada regla que falla lanza una excepción propia (ej. `Overlap`, `PatientNotFound`). El router la captura y devuelve el código HTTP correcto. El servicio nunca decide el HTTP.
- **Baja lógica:** desactivar ≠ borrar. `activo = False` conserva el histórico.

---

## `appointments.py` — núcleo de las citas

El servicio más importante: orquesta todas las reglas al agendar/editar una cita.

| Función | Qué hace |
|---------|----------|
| `create_appointment(...)` | Orquesta el alta: valida servicio/médico/rejilla → no-pasado → upsert del paciente → calcula `ends_at` → valida disponibilidad y anti-solapamiento. `flush`. |
| `edit_appointment(...)` | Edita/mueve una cita activa (parcial), revalidando las mismas reglas y **excluyéndose a sí misma** del anti-solapamiento. |
| `cancel_appointment(...)` | Pasa la cita a `CANCELLED` (libera el cupo). Solo sobre citas activas. |
| `mark_attendance(...)` | Marca `COMPLETED` o `NO_SHOW`. Solo sobre citas activas. |
| `list_appointments(...)` | Agenda por día o rango `[desde, hasta]`, filtrable por médico. |
| `list_patient_appointments(...)` | Historial completo de un paciente. |

**Helpers de validación:** `is_aligned` (rejilla :00/:15/:30/:45), `calculate_ends_at`, `within_availability`, `has_overlap`, `_validate_service_doctor_and_grid`, `_validate_slot`, `_get_active_appointment`, `now_center` (hora del centro, UTC-4).

**Excepciones → HTTP:** `ServiceNotFound`/`DoctorNotFound`/`AppointmentNotFound` → 404 · `TimeNotAligned`/`AppointmentInThePast`/`OutsideAvailability` → 400 · `Overlap`/`AppointmentNotCancellable`/`AppointmentNotActive`/`AppointmentNotEditable` → 409.

---

## `patients.py` — pacientes (CRUD + upsert al agendar)

| Función | Qué hace |
|---------|----------|
| `find_or_create_patient(nombre, edad)` | **Upsert:** busca por `nombre_completo` + `edad`; si existe lo reutiliza, si no lo crea (`rol = PACIENTE`), si hay varios lanza `AmbiguousPatients`. |
| `list_patients` / `get_patient` | Listado (solo activos) y ficha por id. |
| `create_patient` | Alta manual (sin deduplicar); cédula única si se indica. |
| `update_patient` | Edición parcial (solo campos enviados); cédula única. |
| `deactivate_patient` | Baja lógica (`activo = False`). |

**Excepciones:** `PatientNotFound` → 404 · `AmbiguousPatients` → 409 (devuelve la lista de candidatos) · `DuplicateNationalId` → 409.

---

## `catalog.py` — servicios, especialidades y médicos

Alimenta los desplegables del frontend y la gestión de catálogos del ADMIN.

| Función | Qué hace |
|---------|----------|
| `list_services(medico_id=None)` | Servicios activos; con `medico_id` **solo los de las especialidades de ese médico** (evita agendar servicios que no corresponden). |
| `list_doctors` / `list_specialties` | Médicos activos con sus especialidades; catálogo de especialidades. |
| `create_service` / `update_service` | Alta/edición de servicio (ADMIN); permite desactivar sin borrar. |
| `create_specialty` | Alta de especialidad (ADMIN). |

**Excepciones:** `ServiceNotFound` → 404 · `DuplicateName` → 409.

---

## `users.py` — personal que hace login (CRUD, solo ADMIN)

Gestiona ADMIN/RECEPCION/MEDICO. Los pacientes **no** se gestionan aquí (entran por el upsert al agendar).

| Función | Qué hace |
|---------|----------|
| `list_staff` | Todo el personal (excluye pacientes). |
| `get_user` | Usuario por id. |
| `create_user` | Alta con contraseña **hasheada** (bcrypt); el rol no puede ser `PACIENTE`; resuelve especialidades (N:M). |
| `update_user` | Edición parcial; **no permite cambiar el rol** (decisión de diseño); rehashea si cambia la contraseña. |
| `deactivate_user` | Baja lógica. |

**Excepciones:** `UserNotFound` → 404 · `DuplicateEmail`/`RoleNotAllowed` → 409/422 · `SpecialtyNotFound` → 404 · `DoctorOnlyData` (matrícula/especialidades solo para médicos) → 422.

---

## `availability.py` — franjas semanales del médico

| Función | Qué hace |
|---------|----------|
| `list_availability(medico_id)` | Franjas de un médico, ordenadas. |
| `create_availability(...)` | Alta de franja (ADMIN); valida médico y que `hora_inicio < hora_fin`. |

**Excepciones:** `DoctorNotFound` → 404 · `InvalidSlot` → 400.

---

## `common.py` — utilidad compartida

- `value_in_use(db, modelo, columna, valor, excluir_id=None)`: centraliza el patrón de **unicidad** (email, cédula, nombres únicos), excluyendo la propia fila al editar.

---

## Cómo se conecta con el router

```
Router (async)  →  Servicio (lógica)  →  SQLAlchemy (flush)
     │                     │
     │  captura la         │  lanza excepción
     │  excepción y        │  de dominio si
     ▼  devuelve HTTP      ▼  una regla falla
  404/400/409          Overlap, PatientNotFound…
```

El router hace el `db.commit()` final si todo va bien. Ver [`REGLAS-DE-NEGOCIO.md`](REGLAS-DE-NEGOCIO.md) para el detalle de cada regla y [`ARQUITECTURA.md`](ARQUITECTURA.md) para las capas.
