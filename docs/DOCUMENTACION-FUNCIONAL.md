# Documentación Funcional — ERP Diagnóstico

Qué hace el sistema, para quién y bajo qué reglas. Basado en los requisitos reales del centro. Complementa `ROADMAP.md` (plan) y `MODELO-DATOS.md` (datos).

## 1. Objetivo

Dar al centro **Diagnóstico** una herramienta para **gestionar citas médicas** de forma organizada: evitar solapamientos, centralizar los pacientes (hoy dispersos en los contactos del teléfono), agilizar la **confirmación de asistencia** (hoy manual) y dar visión de la agenda desde cualquier sitio.

**Datos del centro:** ~60 citas/día · 18 médicos · ~11-13 especialidades · consultas + ecografías (integral, doppler) + estudios cardíacos.

## 2. Alcance

**Incluye (MVP):**
1. Autenticación con roles (ADMIN, RECEPCION, MEDICO).
2. Gestión de **pacientes** (cédula única si se indica; opcional).
3. **Médicos**, especialidades y **servicios** que ofrece cada médico, con **duración por médico + servicio**.
4. **Disponibilidad** de médicos.
5. Gestión de **citas** con **validación anti-solapamiento** (por médico).
6. **Visita**: agendar en un paso los **varios estudios** del paciente para un día.
7. **Historia clínica** (notas por visita, para reconsultas).
8. **Recordatorios / confirmación por WhatsApp** (el día antes).
9. **Panel**: agenda del día, calendario y métricas.
10. **Auditoría**.

**Fuera del alcance:**
- **Facturación** — se lleva aparte (máquinas fiscales del SENIAT).
- **Portal de pacientes** (los pacientes no acceden).
- **Google Calendar** — por ahora no (la vista móvil de la agenda cubre "consultar desde el teléfono").
- Historia clínica con adjuntos pesados (imágenes/radiografías).

## 3. Usuarios y roles

| Rol | Permisos |
|-----|----------|
| **ADMIN** | Todo: usuarios, médicos, especialidades, servicios y duraciones, tipos, reportes y auditoría. |
| **RECEPCION** | Agenda las citas (WhatsApp, llamada, presencial); gestiona pacientes y visitas; envía/gestiona recordatorios; ve agendas de todos. |
| **MEDICO** | Ve su agenda; marca asistencia/no-show; **consulta y añade notas a la historia clínica** de sus pacientes. |

> Los **pacientes no acceden** al sistema.

## 4. Requisitos funcionales (RF)

| ID | Requisito |
|----|-----------|
| RF-01 | Login con email/contraseña y permisos por rol. |
| RF-02 | ADMIN gestiona usuarios, médicos, especialidades y **servicios**. |
| RF-03 | Por cada médico se define **qué servicios ofrece y su duración** (médico + servicio → minutos). |
| RF-04 | RECEPCION registra y edita **pacientes** (cédula única si se indica; **opcional** para niños/extranjeros). |
| RF-05 | RECEPCION crea, edita, mueve y cancela **citas**. |
| RF-06 | El sistema **impide** solapar dos citas activas del **mismo médico**. |
| RF-07 | La duración/fin de la cita se calcula según el médico + servicio elegido. |
| RF-08 | RECEPCION agenda una **visita** con varios estudios del paciente el mismo día. |
| RF-09 | Los estudios que requieren retiro (holter/MAPA) se agendan como **colocación + retiro** enlazados. |
| RF-10 | El MEDICO ve su agenda y marca **atendida / no-show**. |
| RF-11 | El MEDICO consulta y añade **notas de historia clínica** del paciente. |
| RF-12 | El sistema envía **automáticamente** la confirmación por **WhatsApp** (API de WhatsApp Business) el día antes y registra la respuesta. |
| RF-13 | Panel con agenda del día, calendario y métricas de ocupación. |
| RF-14 | La agenda es **consultable desde el móvil** (vista responsive / PWA). |
| RF-15 | Auditoría de accesos y cambios sobre datos médicos. |

## 5. Requisitos no funcionales (RNF)

| ID | Requisito |
|----|-----------|
| RNF-01 | Seguridad: contraseñas con hash, sesiones seguras, control por rol. |
| RNF-02 | Privacidad HIPAA/GDPR: auditoría; sin credenciales hardcodeadas. |
| RNF-03 | Integridad: cero solapamientos garantizado también en la base de datos. |
| RNF-04 | Rendimiento: soportar el volumen diario (~60 citas/día) con fluidez. |
| RNF-05 | Disponibilidad: acceso remoto (nube) + consulta offline de la agenda (PWA). El centro tiene planta eléctrica, el internet es estable. |
| RNF-06 | Usabilidad: interfaz en español, clara y responsive (uso frecuente desde el móvil). |
| RNF-07 | Mantenibilidad: TypeScript, arquitectura limpia, dominio aislado y testeado. |

## 6. Historias de usuario

**Recepción**
- *Quiero registrar al paciente con su cédula, para no confundir nombres repetidos.*
- *Quiero agendar en un paso los 2-3 estudios del paciente para el mismo día (una visita).*
- *Quiero que el sistema me avise si el horario del médico está ocupado, para no solapar.*
- *Quiero que se envíe solo la confirmación por WhatsApp el día antes, para no hacerlo a mano.*

**Médico**
- *Quiero ver mi agenda del día y marcar asistencia.*
- *Quiero revisar la historia del paciente en una reconsulta o si lo derivan de mi área.*

**Administrador**
- *Quiero definir, por cada médico, qué servicios da y cuánto dura cada uno.*
- *Quiero crear accesos para el personal y ver métricas.*

## 7. Reglas de negocio

| ID | Regla |
|----|-------|
| RN-01 | **Cero solapamientos por médico**: dos citas activas del mismo médico no pueden intersectar en el tiempo. |
| RN-02 | La **duración** de la cita la define la combinación **médico + servicio** (`DoctorServicio.duracionMin`). |
| RN-03 | La **cédula** es única cuando se indica, pero **opcional** (se permite registrar pacientes sin ella). |
| RN-04 | Un médico puede tener **varias especialidades** y varios **servicios** con duraciones distintas. |
| RN-05 | Un paciente puede tener **varias citas el mismo día** (visita); si coinciden en hora, aviso **no bloqueante** (salvo casos como holter). |
| RN-06 | Holter/MAPA: **colocación + retiro** en días distintos, enlazados. |
| RN-07 | Solo se agenda dentro de la **disponibilidad** del médico. |
| RN-08 | Bajas **lógicas** (`activo`), nunca borrado físico. |
| RN-09 | Estados de cita: `SCHEDULED` · `CONFIRMED` (confirmó asistencia) · `CANCELLED` · `COMPLETED` · `NO_SHOW`. |

## 8. Flujo principal: crear una cita / visita

El recorrido completo está en el **flowchart** de [`FLUJO-USUARIO.md`](FLUJO-USUARIO.md). En resumen: seleccionar paciente → añadir uno o varios servicios (con su médico) → el sistema calcula la duración y valida solapamientos → guardar la visita/citas y programar el recordatorio.
