# 🩺 Diagnóstico — ERP de Gestión de Citas Médicas

Sistema interno de gestión de **citas médicas** para el centro de salud **Diagnóstico** (Maracay, Venezuela). Permite al personal gestionar pacientes, médicos, agendas y citas, con **validación estricta de horarios (cero solapamientos)** y protección de datos médicos.

> Proyecto final de bootcamp. Documentación en `docs/`.

---

## 📑 Índice

- [Descripción](#-descripción)
- [Características](#-características)
- [Roles y permisos](#-roles-y-permisos)
- [Stack tecnológico](#-stack-tecnológico)
- [Arquitectura](#-arquitectura)
- [Modelo de datos](#-modelo-de-datos)
- [Regla clave: cero solapamientos](#-regla-clave-cero-solapamientos)
- [Instalación y puesta en marcha](#-instalación-y-puesta-en-marcha)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Roadmap](#-roadmap)
- [Documentación](#-documentación)

---

## 🎯 Descripción

**Diagnóstico** es un ERP interno enfocado en la **gestión, creación y control de citas médicas**. Lo usa únicamente el **personal del centro** (administración, recepción y médicos). Prioriza la seguridad de los datos médicos (HIPAA/GDPR), la validación estricta de horarios y una arquitectura limpia y mantenible.

## ✨ Características

- 📅 **Citas y visitas** — agendar (incluso **varios estudios el mismo día**) con validación anti-solapamiento por médico; holter/MAPA con colocación + retiro.
- 👤 **Pacientes** — alta y gestión (cédula única si se indica; **opcional**).
- 🩺 **Médicos, especialidades y servicios** — con **duración por médico + servicio** y disponibilidad.
- 📋 **Historia clínica** — notas por visita, útiles en reconsultas.
- 💬 **Recordatorios por WhatsApp** — confirmación **automática** el día antes.
- 🔐 **Autenticación y roles** — acceso por rol con control de permisos.
- 📊 **Panel** — agenda del día, calendario y métricas; consultable desde el móvil.
- 📝 **Auditoría** — registro de accesos y cambios sobre datos médicos.

> La **facturación** se lleva aparte (máquinas fiscales del SENIAT). · **Datos:** ~60 citas/día · 18 médicos · ~11-13 especialidades.

## 👥 Roles y permisos

| Rol | Permisos |
|-----|----------|
| **ADMIN** | Control total: usuarios, médicos, especialidades, **servicios y duraciones**, reportes y auditoría. |
| **RECEPCION** | Agenda citas/visitas (WhatsApp, llamada, presencial); gestiona pacientes y recordatorios; ve las agendas de todos. |
| **MEDICO** | Ve su agenda y sus citas; marca asistencia/no-show; consulta y añade notas a la **historia clínica**. |

## 🧱 Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Lenguaje | TypeScript |
| Framework | Next.js (App Router) |
| Base de datos | PostgreSQL |
| ORM | Prisma |
| Estilos | Tailwind CSS |
| Gestor de paquetes | pnpm |
| Runtime | Node.js 22+ |
| Despliegue | Vercel (app) + Neon (PostgreSQL) |

## 🏗️ Arquitectura

- **Nube** — la aplicación y la base de datos viven en la nube (Vercel + Neon), permitiendo **acceso remoto** desde cualquier ordenador.
- **Resiliencia offline** — PWA que cachea la última agenda para **consulta sin conexión** (crear/editar requiere internet). Mitiga la inestabilidad de red.
- **Capa de dominio aislada** — la lógica de citas (incluida la validación anti-solapamiento) vive en `src/server/appointments`, testeable de forma independiente.

## 🗃️ Modelo de datos

Entidades núcleo: `User`, `Doctor`, `Specialty` (N:M), `Servicio` + `DoctorServicio` (**duración por médico**), `Patient`, `Availability`, `Visita`, `Appointment`, `NotaClinica` (historia), `Recordatorio`, `AuditLog`.

📄 Detalle completo y diagrama ER en [`docs/MODELO-DATOS.md`](docs/MODELO-DATOS.md).

## ⛔ Regla clave: cero solapamientos

Una cita nueva o modificada **no puede solaparse en el tiempo** con otra cita activa (`SCHEDULED`/`CONFIRMED`) del mismo médico. Se garantiza en **dos capas**:

1. **Servicio** — validación antes de guardar, con mensaje claro al usuario.
2. **Base de datos** — restricción de exclusión temporal (`EXCLUDE USING gist` sobre `tstzrange`) que rechaza el solapamiento incluso ante operaciones concurrentes.

## 🚀 Instalación y puesta en marcha

> Requisitos: Node.js 22+, pnpm, y una base de datos PostgreSQL (Neon en la nube, recomendado).

```bash
# 1. Clonar e instalar dependencias
git clone <url-del-repo>
cd Diagnostico-Centro-Salud
pnpm install

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env y poner la cadena de conexión de Neon en DATABASE_URL

# 3. Preparar la base de datos
pnpm prisma migrate dev      # aplica migraciones
pnpm prisma db seed          # datos iniciales (usuarios, médicos, servicios)

# 4. Arrancar en desarrollo
pnpm dev                     # http://localhost:3000
```

Otros comandos:

```bash
pnpm build          # construir para producción
pnpm start          # servir la build
pnpm test           # ejecutar tests
pnpm lint           # linting
pnpm prisma studio  # panel visual de la BD
```

> ⚠️ **Nunca** se suben credenciales al repositorio. Todo secreto va en `.env` (ignorado por git).

## 📂 Estructura del proyecto

```
Diagnostico-Centro-Salud/
├── src/
│   ├── app/              # Next.js App Router (rutas + UI, en español)
│   ├── server/           # Lógica de dominio
│   │   ├── appointments/ # Validación anti-solapamiento (aislada, testeable)
│   │   └── auth/         # Autenticación y sesión
│   ├── lib/              # Cliente Prisma, guards de rol, utilidades
│   └── components/       # UI reutilizable (Tailwind)
├── prisma/
│   ├── schema.prisma     # Modelo de datos
│   └── migrations/
├── tests/                # Tests unitarios e integración
├── docs/                 # Documentación del proyecto
├── mockup/               # Prototipo visual navegable (referencia de UI)
└── propuesta/            # Propuesta para el cliente
```

## 🗺️ Roadmap

- [x] Documentación, modelo de datos y prototipo visual
- [ ] **Fase 0** — Andamiaje (Next.js + TS + Tailwind + Prisma + Neon)
- [ ] **Fase 1** — Esquema Prisma + migración + seed
- [ ] **Fase 2** — Autenticación y roles
- [ ] **Fase 3** — Citas y visitas + anti-solapamiento + holter/retiro + tests
- [ ] **Fase 4** — UI (calendario, formularios, pacientes/médicos, visita)
- [ ] **Fase 5** — Historia clínica + recordatorios WhatsApp automáticos
- [ ] **Fase 6** — Panel + PWA (métricas, auditoría, offline)

Detalle en [`docs/ROADMAP.md`](docs/ROADMAP.md).

## 📚 Documentación

| Documento | Contenido |
|-----------|-----------|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Roadmap y planificación: fases, hitos, cronograma (Gantt), kanban y riesgos |
| [`docs/DOCUMENTACION-FUNCIONAL.md`](docs/DOCUMENTACION-FUNCIONAL.md) | Requisitos, roles e historias de usuario |
| [`docs/CASOS-DE-USO.md`](docs/CASOS-DE-USO.md) | Diagrama y descripción de casos de uso (Mermaid) |
| [`docs/FLUJO-USUARIO.md`](docs/FLUJO-USUARIO.md) | Flowchart del flujo de usuario (Mermaid) |
| [`docs/MODELO-DATOS.md`](docs/MODELO-DATOS.md) | Entidades, campos, relaciones, diagrama ER y reglas |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Arquitectura, capas, flujo de datos y decisiones técnicas |
| [`docs/MANUAL-USUARIO.md`](docs/MANUAL-USUARIO.md) | Guía de uso paso a paso para el personal |
| [`propuesta/`](propuesta/) | Propuesta para el cliente (PDF) |

---

*Desarrollado como proyecto final de bootcamp — Centro de Salud Diagnóstico, Maracay.*
