# ERP Diagnóstico — Mejoras y Próximos Pasos

> El MVP cubre el **núcleo** (agendar citas con cero solapamientos, validación de disponibilidad,
> gestión de pacientes/médicos/servicios) y está **probado y desplegado**. Este documento
> reúne, en un solo lugar, **hacia dónde puede crecer** el proyecto: lo inmediato, las
> funcionalidades de fase 2 y la deuda técnica anotada durante el desarrollo.

## 1. Próximos pasos inmediatos

Cosas ya preparadas o de bajo esfuerzo, para dejar el producto redondo:

- **Despliegue de las mejoras (v0.6.0):** publicar en producción el filtro de servicios por especialidad (N:M), el *delete* de pacientes/usuarios y el renombrado del código a inglés.
- **Botón "Desactivar" en la ficha del paciente (frontend):** el endpoint `DELETE /pacientes/{id}` ya existe; falta el botón en la UI.
- **Contrato de la API en inglés (decisión abierta):** el **código** ya está en inglés; queda el **contrato** (rutas, campos JSON, valores de enum, tablas/columnas). Se hace **coordinado backend + frontend** por su impacto; se documenta como decisión de dominio (la UI y el contrato pueden quedarse en español, que es el idioma del centro).

## 2. Fase 2 — Funcionalidades (fuera del MVP)

Funcionalidad de valor que se dejó **conscientemente fuera** para cumplir el plazo, con la base ya preparada:

| Mejora | Nota |
|--------|------|
| **Historia clínica / notas clínicas** | La tabla `notas_clinicas` ya existe como andamiaje; el médico escribiría la evolución por paciente/cita. |
| **Reportes y estadísticas** | Citas por médico/servicio/periodo, no-shows, ocupación. |
| **Recordatorios por WhatsApp** | Aviso automático al paciente antes de la cita. |
| **Auditoría / log de cambios** | Registro de quién crea/edita/cancela (traza completa). |
| **Visitas (agrupar estudios)** | Varios estudios de un paciente en una misma visita. |
| **Duración por médico/servicio** | Duraciones por defecto según el tipo de estudio o el médico. |
| **Recursos / salas** | Anti-solapamiento también por **recurso** (el ecógrafo y los consultorios son el cuello de botella real, no solo el médico). |
| **Holter: colocación + retiro** | Modelar el estudio en dos momentos. |
| **Portal de pacientes** | Que el paciente consulte/gestione sus citas. |
| **Integración con Google Calendar** | Sincronizar la agenda del médico. |
| **PWA offline** | Uso básico sin conexión en recepción. |

*Facturación:* **fuera del sistema** (SENIAT, pago directo); no es un pendiente del ERP.

## 3. Deuda técnica (anotada en la revisión)

Detalles detectados que **no bloquean el MVP** pero conviene resolver:

- **Validación de franjas de disponibilidad:** `create_availability` no comprueba franjas duplicadas o solapadas por médico y día.
- **Paginación:** los listados de pacientes/personal aún no paginan.
- **Unicidad sensible a mayúsculas/acentos** en `nombre`/`email`/`cédula` (normalizar antes de comparar).
- **CORS multi-origen:** permitir a la vez el entorno local y el de producción.
- **Anti-solapamiento a nivel BD:** añadir un constraint `gist` como red de seguridad además de la validación en la capa de servicio.
- **Identificación robusta del paciente:** hoy se identifica por `nombre_completo` + `edad` (posibles duplicados); reforzar con `fecha_nacimiento` obligatoria y/o `cédula`.
- **Convención de fechas** *(ya resuelta y documentada):* la API trabaja en hora local naive y **rechaza fechas con zona (422)**; el "ahora" se calcula en hora del centro (UTC-4) para no descuadrar en un servidor UTC.

---

> Ver también: [`ROADMAP.md`](ROADMAP.md) (fases y planificación) · [`MODELO-DATOS.md`](MODELO-DATOS.md) (andamiaje de fase 2).
