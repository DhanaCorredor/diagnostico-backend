# Resumen del proyecto — ERP Diagnóstico

Punto de entrada a la documentación. Resume qué es el proyecto, su estado y enlaza al resto de documentos.

## ¿Qué es?

**ERP interno para el centro de salud "Diagnóstico"** (Maracay, Aragua — Venezuela), centrado en la **gestión y creación de citas médicas**: login por roles, validación estricta de horarios (cero solapamientos por médico), bloqueo por disponibilidad y gestión centralizada de pacientes.

- **Autora:** Dhana Corredor (proyecto final).
- **Dos repositorios:** backend (este, `diagnostico-backend`) y frontend (`diagnostico-frontend`, aparte).

## Stack

- **Backend:** Python + FastAPI + SQLAlchemy + Alembic · PostgreSQL
- **Frontend:** React (Vite, JavaScript) + React Router · Tailwind CSS · pnpm
- **Auth:** JWT propio (contraseñas con bcrypt)
- **Despliegue:** Render (API + PostgreSQL gestionado)

## Estado actual

- **Backend: completo** y desplegado en **Render** (release **v0.4.1**; el catálogo final va en **v0.5.0**, pendiente de confirmación de la clienta).
- **97 tests** en verde (unitarios + integración).
- **Frontend: pendiente** (Fase 4, repo aparte).

## Datos del sistema

- **Roles:** ADMIN · RECEPCIÓN · MEDICO (solo personal interno hace login; los pacientes son registros).
- **17 médicos** · **12 especialidades**.
- **45 servicios** en 6 categorías: Consultas (11) · Ecografías (10) · Doppler (12) · Estudios cardíacos (5) · Promociones (5) · Otros (2).
- **Pacientes:** upsert al agendar por `nombre_completo + edad`; cédula opcional.
- **Fuera del MVP (fase 2):** facturación/precios, historia clínica, recordatorios WhatsApp, reportes, PWA, recursos/salas.

## Índice de la documentación

| Documento | Contenido |
|-----------|-----------|
| [ARQUITECTURA.md](ARQUITECTURA.md) | Arquitectura, capas y decisiones técnicas |
| [DOCUMENTACION-FUNCIONAL.md](DOCUMENTACION-FUNCIONAL.md) | Qué hace el sistema, roles y requisitos funcionales (RF) |
| [MODELO-DATOS.md](MODELO-DATOS.md) | Modelo de datos (7 tablas), diagrama ER y reglas |
| [REGLAS-DE-NEGOCIO.md](REGLAS-DE-NEGOCIO.md) | Reglas de negocio (solapamiento, disponibilidad, estados) |
| [CASOS-DE-USO.md](CASOS-DE-USO.md) | Casos de uso por rol |
| [FLUJO-USUARIO.md](FLUJO-USUARIO.md) | Flujo del usuario (flowchart) |
| [MANUAL-USUARIO.md](MANUAL-USUARIO.md) | Manual de uso paso a paso |
| [COMPONENTES.md](COMPONENTES.md) | Componentes del frontend previstos |
| [DESPLIEGUE.md](DESPLIEGUE.md) | Despliegue en Render (build, seed, variables) |
| [ROADMAP.md](ROADMAP.md) | Plan, fases, cronograma y checklist de endpoints (§3.1) |

> El *briefing* del cliente (`BRIEFING.md`) es un documento histórico **local** (no versionado, contiene datos del cliente).
