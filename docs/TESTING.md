# ERP Diagnóstico — Documentación de Testing

> **100 tests** con `pytest`, verdes en cada commit. Cubren la **lógica de negocio**
> (tests unitarios sobre la capa de servicios) y el **contrato HTTP** (tests de integración
> con `TestClient`, incluyendo auth y permisos por rol).

## ¿Por qué se hicieron estos tests?

El valor del sistema está en unas reglas **críticas**: un fallo no es un detalle estético, es un **médico con dos citas a la misma hora** o una cita agendada fuera de su horario. Por eso se testea:

1. **Garantizar las reglas de negocio.** Cada test comprueba que una regla real se cumple (cero solapamientos, disponibilidad, rejilla de minutos, no agendar en el pasado, roles). Son la traducción ejecutable de [`REGLAS-DE-NEGOCIO.md`](REGLAS-DE-NEGOCIO.md).
2. **Red de seguridad ante cambios (regresión).** Los tests permiten refactorizar sin miedo: si algo se rompe, saltan. **Ejemplo real de este proyecto:** durante el renombrado masivo del código a inglés (cientos de identificadores, archivos y clases), los **100 tests en verde en cada paso** demostraron que el comportamiento no cambió ni una coma.
3. **Cubrir los casos límite, no solo el camino feliz.** Se prueban también los errores esperados (paciente ambiguo, cédula duplicada, cita ya cancelada, rol sin permiso) y los bordes finos (citas **pegadas** que no se solapan, edición que no choca **consigo misma**).

**Trazabilidad regla → test (ejemplos):**

| Regla de negocio | Test que la garantiza |
|------------------|-----------------------|
| R4 · Cero solapamientos por médico | `test_create_appointment_blocks_overlap`, `test_overlap_and_adjacent_appointments` |
| R3 · Dentro de la disponibilidad | `test_create_appointment_outside_availability`, `test_availability_inside_and_outside` |
| R0 · Rejilla :00/:15/:30/:45 | `test_create_appointment_unaligned_time` |
| R0.b · No agendar en el pasado | `test_create_appointment_in_the_past` |
| R1 · Upsert de paciente | `test_creates_if_not_exists`, `test_reuses_if_exists`, `test_multiple_matches_raises_ambiguous` |
| Permisos por rol | `test_doctor_cannot_create_appointment`, `test_reception_cannot_see_users`, `test_reception_cannot_edit_availability` |
| R7 · Franjas que no se solapan | `test_create_availability_overlapping_slot`, `test_create_availability_contiguous_slots_allowed`, `test_update_availability_does_not_clash_with_itself` |
| R8 · No dejar citas fuera de horario | `test_delete_availability_blocked_when_it_has_bookings`, `test_update_availability_blocked_when_it_strands_a_booking`, `test_update_availability_allowed_when_the_booking_still_fits` |

## Estrategia

Dos niveles, para probar cada cosa en su capa:

1. **Unitarios (capa de servicios):** llaman directamente a `create_appointment`, `find_or_create_patient`, etc. con una sesión de BD. Prueban las reglas de negocio **sin levantar la API** → rápidos y precisos.
2. **Integración (HTTP):** usan `TestClient` de FastAPI para pegarle a los endpoints reales, con token JWT. Prueban el contrato completo: códigos de estado, guardas por rol, y el flujo punta a punta de una cita.

## Aislamiento: cada test en una transacción que se revierte

`conftest.py` monta el fixture `db` sobre una **transacción con savepoints** que se **revierte al terminar** (`rollback`). Los `commit()` que hacen los endpoints se confinan a un SAVEPOINT, así **ningún test deja rastro** en la base de datos y se pueden correr en cualquier orden.

**Fixtures de apoyo:** `db` (sesión aislada), `client` (TestClient con la BD del test inyectada), `token_for` (cabecera `Authorization` de un usuario), y datos de prueba (`admin`, `recepcion`, `doctor`, `service`).

## Qué cubre cada archivo

| Archivo | Tests | Cubre |
|---------|:---:|-------|
| `test_appointments.py` | 46 | El **núcleo**: rejilla de minutos, no-pasado, médico/servicio activos, upsert de paciente, duración elegida, disponibilidad, **anti-solapamiento** (incl. citas pegadas y edición que no se solapa consigo misma), la **restricción de exclusión de la base de datos**, cancelar, marcar asistencia, editar/mover, rechazo de fechas con zona horaria. |
| `test_availability.py` | 22 | CRUD de franjas: crear/listar, franja inválida, médico inválido, **franjas solapadas** (y contiguas permitidas), edición parcial, y que **borrar o reducir no deje citas fuera de horario** (ignorando canceladas y pasadas). |
| `test_users.py` | 17 | CRUD de personal (ADMIN): alta con hash de contraseña, email duplicado (también ignorando mayúsculas), rol PACIENTE no permitido, especialidades solo para médicos, baja/reactivación, y **guardas por rol** (recepción no ve usuarios). |
| `test_integration.py` | 17 | **HTTP punta a punta:** login y `/me`, login ignorando mayúsculas, token inválido, flujo completo de una cita, paciente ambiguo devuelve candidatos, borrado de franja por ADMIN, y que el MÉDICO no cree/cancele/marque asistencia. |
| `test_catalog.py` | 16 | Servicios y especialidades: listar solo activos y ordenados, **filtro por médico** (N:M), crear/editar/desactivar, nombres duplicados **ignorando mayúsculas y tildes** (y que nombres distintos de verdad sigan permitidos). |
| `test_patients.py` | 12 | Upsert (reutiliza/crea/ambiguo), alta manual, edición parcial que no borra la cédula, cédula duplicada (también ignorando mayúsculas), baja lógica. |
| `test_main.py` | 7 | Configuración de la aplicación: troceo de orígenes CORS, cabeceras para un origen autorizado y para uno que no lo está, y `/health` con la base viva y caída. |
| `test_db.py` | 2 | Que el *engine* comprueba las conexiones antes de usarlas (`pool_pre_ping`) y que alcanza la base. |
| **Total** | **139** | |

## Técnicas destacadas

- **Inyección del tiempo:** las reglas que dependen de "ahora" (no agendar en el pasado) reciben un parámetro `ahora` inyectable, así el test fija la hora y es **determinista**.
- **Rechazo de `datetime` con zona:** el schema rechaza fechas *tz-aware* (el sistema trabaja en hora local del centro, naive); hay tests que lo verifican en `create` y `update`.
- **Anti-solapamiento fino:** se prueba que dos citas **pegadas** (una acaba cuando empieza la otra) **no** se solapan, y que al **editar** una cita no choca **consigo misma**.
- **Guardas por rol:** varios tests comprueban que un rol sin permiso recibe **403**, no solo que el camino feliz funciona.

## Ejecutar

```bash
pytest            # los 100 tests
pytest -q         # salida compacta
pytest tests/test_appointments.py::test_create_appointment_blocks_overlap   # uno solo
```
