# 🩺 Diagnóstico — Medical Appointment Management ERP

[![CI](https://github.com/DhanaCorredor/diagnostico-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/DhanaCorredor/diagnostico-backend/actions/workflows/ci.yml)

Internal **medical appointment** management system for the **Diagnóstico** health center (Maracay, Venezuela). It lets the staff log in by role and manage patients, doctors and appointments, with **strict schedule validation (zero overlaps per doctor)** and **availability-aware scheduling**.

> Bootcamp final project, delivered. Documentation in `docs/` (in Spanish).
>
> **Status:** the backend is **complete and deployed** — [live API](https://diagnostico-api-jtbw.onrender.com/docs) (release **v0.9.0**, auto-deploy on push to `main`). Every entity has a full CRUD and **159 passing tests** (unit + integration) run on every push by CI. The API runs on Render, its PostgreSQL database on Neon and the React frontend (`diagnostico-frontend`) on Vercel.

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

> **Out of MVP (phase 2):** clinical history, reports, reminders, audit log, rooms/resources and more — full list in [`docs/MEJORAS-Y-PROXIMOS-PASOS.md`](docs/MEJORAS-Y-PROXIMOS-PASOS.md). **Billing** is handled separately (SENIAT); direct payment only.

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

Core entities (8 tables): `usuarios` (unified), `especialidades` + `usuario_especialidad` (N:M), `servicios` + `servicio_especialidad` (N:M), `disponibilidad`, `citas` (zero overlaps per doctor), `notas_clinicas` (reserved for phase 2, out of MVP).

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
pytest                       # run the test suite

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
│   ├── auth.py          # JWT, hashing, role guard
│   ├── enums/           # Role, AppointmentStatus, ServiceCategory
│   ├── models/          # SQLAlchemy models (one file per table)
│   ├── schemas/         # Pydantic schemas
│   ├── controller/      # routers: auth, users, appointments, catalog, availability, patients
│   └── services/        # business logic (appointments, patients, catalog…)
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

## 🗺️ Status

The MVP is **delivered and running in production**: the API on Render, its PostgreSQL database on
Neon and the React frontend on Vercel, all on free plans with no expiry date.

Every entity has a full CRUD, the appointment rules are enforced both in the service layer and by
a database constraint, and the whole suite runs on every push.

What is done and what is still open — with the reasoning behind each decision — lives in a single
place: [`docs/MEJORAS-Y-PROXIMOS-PASOS.md`](docs/MEJORAS-Y-PROXIMOS-PASOS.md).

## 📚 Documentation

> Documentation is written in Spanish (project language); this README is in English.

| Document | Content |
|----------|---------|
| [`docs/DOCUMENTACION-FUNCIONAL.md`](docs/DOCUMENTACION-FUNCIONAL.md) | What the system does: requirements, roles, use cases and the decisions behind them |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | How it is built: layers, data flow, the service layer, patterns and technical decisions |
| [`docs/MODELO-DATOS.md`](docs/MODELO-DATOS.md) | Entities, fields, relations, ER diagram and rules |
| [`docs/REGLAS-DE-NEGOCIO.md`](docs/REGLAS-DE-NEGOCIO.md) | Canonical business rules and how they are implemented |
| [`docs/MANUAL-USUARIO.md`](docs/MANUAL-USUARIO.md) | Step-by-step usage guide for the staff, with the user flow |
| [`docs/TESTING.md`](docs/TESTING.md) | Testing strategy and what the tests cover |
| [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md) | Deployment guide (Render + Neon + Vercel) |
| [`docs/MEJORAS-Y-PROXIMOS-PASOS.md`](docs/MEJORAS-Y-PROXIMOS-PASOS.md) | The work catalogue: what is done, what is pending and the API contract |

---

*Developed as a bootcamp final project — Centro de Salud Diagnóstico, Maracay.*
