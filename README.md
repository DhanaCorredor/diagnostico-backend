# 🩺 Diagnóstico — Medical Appointment Management ERP

Internal **medical appointment** management system for the **Diagnóstico** health center (Maracay, Venezuela). It lets the staff log in by role and manage patients, doctors and appointments, with **strict schedule validation (zero overlaps per doctor)** and **availability-aware scheduling**.

> Bootcamp final project — MVP scoped to a 2-week deadline. Documentation in `docs/` (in Spanish).
>
> **Status:** the backend MVP is **complete and deployed** — [live API](https://diagnostico-api-jtbw.onrender.com/docs) (release **v0.4.1** on Render, auto-deploy on push to `main`). 97 passing tests (unit + integration). The React frontend (`diagnostico-frontend`) is the remaining phase.

---

## 📑 Table of contents

- [Overview](#-overview)
- [Features](#-features)
- [Roles and permissions](#-roles-and-permissions)
- [Tech stack](#-tech-stack)
- [Architecture](#-architecture)
- [Data model](#-data-model)
- [Core rules](#-core-rules)
- [Getting started](#-getting-started)
- [Project structure](#-project-structure)
- [Roadmap](#-roadmap)
- [Documentation](#-documentation)

---

## 🎯 Overview

**Diagnóstico** is an internal ERP focused on **managing and creating medical appointments**. It is used only by the **center's staff** (administration, reception and doctors). It prioritizes medical-data security, strict schedule validation and a simple, maintainable architecture.

## ✨ Features

- 🔐 **Authentication & roles** — login (JWT) with role-based access control.
- 👥 **Unified users table** — staff, doctors and patients share one `usuarios` table (by `rol`); the UI keeps **two separate views** (Patients and Doctors).
- 👤 **Patients** — registration and management (national ID unique when provided; **optional**), with **automatic upsert when booking** (detect if exists, create if not).
- 🩺 **Doctors** — specialties (**N:M**) and **weekly availability**.
- 📅 **Appointments & calendar** — book with **overlap validation per doctor** and **availability-based blocking** (days/hours the doctor is off are not selectable).

> **Out of MVP (phase 2):** clinical history / doctor's notes, reports, WhatsApp reminders, audit log, visits (grouped studies), per-doctor duration, rooms/resources + resource overlap, Holter placement/removal, PWA offline. · **Billing** is handled separately (SENIAT); **direct payment only**.

## 👥 Roles and permissions

| Role | Permissions |
|------|-------------|
| **ADMIN** | Full control: users, doctors, specialties, services, configuration. |
| **RECEPCION** | Books and cancels appointments; marks attendance (attended/no-show); manages patients; **views** doctors and agendas. **No** access to **users**, **configuration** or **reports**. |
| **MEDICO** | Sees their own agenda (**read-only**). Cannot cancel or mark attendance — reception/admin does that. *(Clinical history notes are phase 2.)* |

> Patients do **not** log in (they are records managed by reception).

## 🧱 Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | **Python + FastAPI** |
| ORM | **SQLAlchemy** (+ Alembic migrations) |
| Database | **PostgreSQL** |
| Auth | **JWT** (bcrypt password hashing) |
| Frontend | **React (Vite, JavaScript)** + React Router |
| Styling | Tailwind CSS |
| Package manager | **pnpm** (frontend) · pip (backend) |

> No Prisma, no Next.js, no TypeScript.

## 🏗️ Architecture

- **Two repositories** — the **frontend** (React, `diagnostico-frontend`) and this **backend** (FastAPI) are separate repos; the project docs live here, in the backend repo.
- **Decoupled** — the React SPA (Vite) talks to the FastAPI REST API over HTTP/JSON, authenticated with a **JWT** bearer token.
- **Business logic in the service layer** — appointment validation (overlap per doctor, availability) and patient upsert live in `app/services`, independently testable.
- **Two UI views over one table** — Patients and Doctors are filtered views of the unified `usuarios` table.

## 🗃️ Data model

Core entities (7 tables): `usuarios` (unified), `especialidades` + `usuario_especialidad` (N:M), `servicios`, `disponibilidad`, `citas` (zero overlaps per doctor), `notas_clinicas` (reserved for phase 2, out of MVP).

📄 Full detail and ER diagram in [`docs/MODELO-DATOS.md`](docs/MODELO-DATOS.md).

## ⛔ Core rules

- **Zero overlaps (per doctor)** — a new/modified appointment cannot overlap in time with another active appointment (`SCHEDULED`/`CONFIRMED`) of the same doctor. Validated in the backend service layer before saving.
- **Availability** — appointments can only be booked inside the doctor's weekly availability; the calendar blocks the rest.
- **Patient upsert** — booking identifies the patient by **full name + age** and creates one if none exists (the national ID is optional, added later by specialists).

## 🚀 Getting started

> Requirements: Python 3.12+, Node.js 20+ with pnpm, and a PostgreSQL database (a local install, or a managed cloud Postgres — Render in production).

```bash
# Backend (this repo)
git clone <backend-repo-url> && cd diagnostico-backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # set DATABASE_URL, JWT_SECRET and ADMIN_PASSWORD
alembic upgrade head         # apply migrations
python -m app.seed           # seed catalogs + staff login users (needs ADMIN_PASSWORD)
uvicorn app.main:app --reload   # http://localhost:8000  (Swagger at /docs)
pytest                       # run the test suite (97 tests)

# Frontend (separate repo, in another terminal)
git clone <frontend-repo-url> && cd diagnostico-frontend
pnpm install
pnpm dev                     # http://localhost:5173
```

> ⚠️ **Never** commit credentials to the repository. Every secret goes in `.env` (git-ignored).

## 📂 Project structure

**Backend repo** (`diagnostico-backend`, this one):

```
├── app/
│   ├── main.py          # FastAPI app + routers
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # JWT, hashing, role guard
│   ├── routers/         # auth, usuarios, citas, catalogo, disponibilidad, pacientes
│   └── services/        # appointment & patient logic
├── alembic/             # migrations
├── tests/               # pytest
├── requirements.txt
├── docs/                # project documentation (Spanish)
└── mockup/              # clickable visual prototype (UI reference)
```

**Frontend repo** (`diagnostico-frontend`):

```
└── src/
    ├── api/             # HTTP client + token
    ├── pages/           # login, agenda, patients, doctors
    └── components/      # reusable UI (Tailwind)
```

## 🗺️ Roadmap

- [x] Documentation, unified data model and visual prototype
- [x] **Phase 0** — Scaffolding (FastAPI backend here + React/Vite frontend in its own repo)
- [x] **Phase 1** — SQLAlchemy models + Alembic migration + seed
- [x] **Phase 2** — Authentication (JWT) and roles
- [x] **Phase 3** — Appointments core (patient upsert + availability + overlap per doctor) + tests
- [ ] **Phase 4** — UI (login, calendar, Patients/Doctors views, appointment form) — frontend repo, pending
- [x] **Phase 5** — Deployment (backend live on Render, release v0.4.1)

Details in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## 📚 Documentation

> Documentation is written in Spanish (project language); this README is in English.

| Document | Content |
|----------|---------|
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Roadmap and planning: phases, schedule (Gantt), kanban and risks |
| [`docs/DOCUMENTACION-FUNCIONAL.md`](docs/DOCUMENTACION-FUNCIONAL.md) | Requirements, roles, user stories and use cases |
| [`docs/FLUJO-USUARIO.md`](docs/FLUJO-USUARIO.md) | User-flow flowchart (Mermaid) |
| [`docs/MODELO-DATOS.md`](docs/MODELO-DATOS.md) | Entities, fields, relations, ER diagram and rules |
| [`docs/REGLAS-DE-NEGOCIO.md`](docs/REGLAS-DE-NEGOCIO.md) | Canonical business rules and how they are implemented |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Architecture, layers, data flow and technical decisions |
| [`docs/MANUAL-USUARIO.md`](docs/MANUAL-USUARIO.md) | Step-by-step usage guide for the staff |
| [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md) | Deployment guide (Render + PostgreSQL) |

---

*Developed as a bootcamp final project — Centro de Salud Diagnóstico, Maracay.*
