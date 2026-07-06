# 🩺 Diagnóstico — Medical Appointment Management ERP

Internal **medical appointment** management system for the **Diagnóstico** health center (Maracay, Venezuela). It lets the staff manage patients, doctors, schedules and appointments, with **strict schedule validation (zero overlaps)** and protection of medical data.

> Bootcamp final project. Documentation in `docs/` (in Spanish).

---

## 📑 Table of contents

- [Overview](#-overview)
- [Features](#-features)
- [Roles and permissions](#-roles-and-permissions)
- [Tech stack](#-tech-stack)
- [Architecture](#-architecture)
- [Data model](#-data-model)
- [Core rule: zero overlaps](#-core-rule-zero-overlaps)
- [Getting started](#-getting-started)
- [Project structure](#-project-structure)
- [Roadmap](#-roadmap)
- [Documentation](#-documentation)

---

## 🎯 Overview

**Diagnóstico** is an internal ERP focused on **managing, creating and controlling medical appointments**. It is used only by the **center's staff** (administration, reception and doctors). It prioritizes medical-data security (HIPAA/GDPR), strict schedule validation and a clean, maintainable architecture.

## ✨ Features

- 📅 **Appointments & visits** — schedule (even **several studies on the same day**) with overlap validation **per doctor and per room/resource (consultorio/sala/equipo)**; Holter/MAPA as placement + removal.
- 👤 **Patients** — registration and management (national ID unique when provided; **optional**).
- 🩺 **Doctors, specialties and services** — with **duration per doctor + service** and availability.
- 📋 **Clinical history** — notes per visit, useful for follow-up consultations.
- 💬 **WhatsApp reminders** — **automatic** confirmation 24 h before the appointment.
- 🔐 **Authentication & roles** — role-based access control.
- 📊 **Dashboard** — today's agenda, calendar and reports; accessible from mobile.
- 📝 **Audit log** — record of access and changes to medical data.

> **Billing** is handled separately (SENIAT fiscal machines); **direct payment only, no insurance**. · **Figures:** ~60 appointments/day · 18 doctors · ~11-13 specialties · single location.

## 👥 Roles and permissions

| Role | Permissions |
|------|-------------|
| **ADMIN** | Full control: users, doctors, specialties, **services and durations**, rooms/resources, reports and audit. |
| **RECEPCION** | Books appointments/visits (WhatsApp, call, in person); manages patients and reminders; sees everyone's agenda. |
| **MEDICO** | Sees their own agenda and appointments; marks attendance/no-show; reads and adds notes to the **clinical history**. |

## 🧱 Tech stack

| Layer | Technology |
|-------|-----------|
| Language | TypeScript |
| Framework | Next.js (App Router) |
| Database | PostgreSQL |
| ORM | Prisma |
| Styling | Tailwind CSS |
| Package manager | pnpm |
| Runtime | Node.js 22+ |
| Deployment | Vercel (app) + Neon (PostgreSQL) |

## 🏗️ Architecture

- **Cloud** — the app and the database live in the cloud (Vercel + Neon), enabling **remote access** from any computer.
- **Offline resilience** — a PWA caches the latest agenda for **offline reading** (creating/editing requires internet). Mitigates network instability.
- **Isolated domain layer** — the appointment logic (including overlap validation) lives in `src/server/appointments`, independently testable.

## 🗃️ Data model

Core entities: `User`, `Doctor`, `Specialty` (N:M), `Servicio` + `DoctorServicio` (**duration per doctor**), `Recurso` (room/space/equipment), `Patient`, `Availability`, `Visita`, `Appointment`, `NotaClinica` (clinical history), `Recordatorio` (reminder), `AuditLog`.

📄 Full detail and ER diagram in [`docs/MODELO-DATOS.md`](docs/MODELO-DATOS.md).

## ⛔ Core rule: zero overlaps

A new or modified appointment **cannot overlap in time** with another active appointment (`SCHEDULED`/`CONFIRMED`) that shares the same doctor or the same room/resource. This is guaranteed at **two layers**:

1. **Service layer** — validation before saving, with a clear message to the user.
2. **Database** — temporal exclusion constraints (`EXCLUDE USING gist` over `tstzrange`) that reject overlaps even under concurrent operations.

## 🚀 Getting started

> Requirements: Node.js 22+, pnpm, and a PostgreSQL database (Neon in the cloud, recommended).

```bash
# 1. Clone and install dependencies
git clone <repo-url>
cd Diagnostico-Centro-Salud
pnpm install

# 2. Configure environment variables
cp .env.example .env
# Edit .env and set the Neon connection string in DATABASE_URL

# 3. Prepare the database
pnpm prisma migrate dev      # apply migrations
pnpm prisma db seed          # seed data (users, doctors, services)

# 4. Run in development
pnpm dev                     # http://localhost:3000
```

Other commands:

```bash
pnpm build          # build for production
pnpm start          # serve the build
pnpm test           # run tests
pnpm lint           # linting
pnpm prisma studio  # visual DB panel
```

> ⚠️ **Never** commit credentials to the repository. Every secret goes in `.env` (git-ignored).

## 📂 Project structure

```
Diagnostico-Centro-Salud/
├── src/
│   ├── app/              # Next.js App Router (routes + UI, in Spanish)
│   ├── server/           # Domain logic
│   │   ├── appointments/ # Overlap validation (isolated, testable)
│   │   └── auth/         # Authentication and session
│   ├── lib/              # Prisma client, role guards, utilities
│   └── components/       # Reusable UI (Tailwind)
├── prisma/
│   ├── schema.prisma     # Data model
│   └── migrations/
├── tests/                # Unit and integration tests
├── docs/                 # Project documentation (Spanish)
└── mockup/               # Clickable visual prototype (UI reference)
```

## 🗺️ Roadmap

- [x] Documentation, data model and visual prototype
- [ ] **Phase 0** — Scaffolding (Next.js + TS + Tailwind + Prisma + Neon)
- [ ] **Phase 1** — Prisma schema + migration + seed
- [ ] **Phase 2** — Authentication and roles
- [ ] **Phase 3** — Appointments & visits + overlap prevention + Holter/removal + tests
- [ ] **Phase 4** — UI (calendar, forms, patients/doctors, visit)
- [ ] **Phase 5** — Clinical history + automatic WhatsApp reminders
- [ ] **Phase 6** — Dashboard + PWA (reports, audit, offline)

Details in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## 📚 Documentation

> Documentation is written in Spanish (project language); this README is in English.

| Document | Content |
|----------|---------|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Roadmap and planning: phases, milestones, schedule (Gantt), kanban and risks |
| [`docs/DOCUMENTACION-FUNCIONAL.md`](docs/DOCUMENTACION-FUNCIONAL.md) | Requirements, roles and user stories |
| [`docs/CASOS-DE-USO.md`](docs/CASOS-DE-USO.md) | Use-case diagram and description (Mermaid) |
| [`docs/FLUJO-USUARIO.md`](docs/FLUJO-USUARIO.md) | User-flow flowchart (Mermaid) |
| [`docs/MODELO-DATOS.md`](docs/MODELO-DATOS.md) | Entities, fields, relations, ER diagram and rules |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Architecture, layers, data flow and technical decisions |
| [`docs/MANUAL-USUARIO.md`](docs/MANUAL-USUARIO.md) | Step-by-step usage guide for the staff |

---

*Developed as a bootcamp final project — Centro de Salud Diagnóstico, Maracay.*
