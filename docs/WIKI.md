# 🩺 ERP Diagnóstico — Wiki del Proyecto

> **Sistema interno de gestión de citas médicas** — Centro de Salud Diagnóstico, Maracay 🇻🇪
> Proyecto final de bootcamp · Portada y **resumen** del proyecto (el detalle está en cada subpágina).

---

## 🚀 Resumen del proyecto

ERP interno para **gestionar, crear y controlar citas médicas**. Lo usa solo el **personal del centro** (administración, recepción y médicos). Su función estrella es la **validación de horarios con cero solapamientos**, con protección de datos médicos (HIPAA/GDPR).

| | |
|---|---|
| **¿Qué es?** | ERP de citas para personal interno. |
| **Función estrella** | Cero solapamientos de citas. |
| **Arquitectura** | Nube (Vercel + Neon) + PWA con lectura offline. |
| **Alcance MVP** | Auth · pacientes · médicos/servicios (duración por médico) · citas y visitas · historia clínica · recordatorios WhatsApp · panel · auditoría. |
| **Volumen** | ~60 citas/día · 18 médicos · ~11-13 especialidades. |
| **Estado** | 📄 Documentación completa · ⏳ Desarrollo pendiente. |

## ✨ Funcionalidades
**Citas y visitas** (varios estudios el mismo día, anti-solapamiento por médico) · **pacientes** (cédula opcional) · **médicos**, especialidades y **servicios** (duración por médico) · **historia clínica** · **recordatorios automáticos por WhatsApp** · **panel** y métricas (vista móvil) · **auditoría**. *(La facturación va aparte, con máquinas fiscales del SENIAT.)*

## 👥 Roles
🛡️ **Administrador** — control total · 🗂️ **Recepción** — pacientes y citas · 🩺 **Médico** — su agenda.

## 🧱 Stack
`TypeScript` · `Next.js (App Router)` · `PostgreSQL + Prisma` · `Tailwind CSS` · `pnpm` · `Node 22+` · Despliegue: `Vercel + Neon`.

---

## 📚 Índice de la documentación

> 💡 En Notion, cada fila es una **subpágina**. Enlázalas escribiendo `@` + el nombre.

| 📄 Página | Contenido |
|-----------|-----------|
| 🗺️ **Roadmap y planificación** | Decisiones, alcance, fases, hitos, cronograma (Gantt), kanban y riesgos |
| 📌 **Documentación funcional** | Objetivo, alcance, requisitos (RF/RNF), roles, historias de usuario y reglas |
| 🎭 **Casos de uso** | Actores × acciones (diagrama) y descripciones |
| 🔀 **Flujo de usuario** | Recorrido por rol + subflujo de crear cita (flowchart) |
| 🗃️ **Modelo de datos** | Entidades, campos, relaciones y diagrama ER |
| 🏗️ **Arquitectura** | Capas, componentes, estructura de carpetas y decisiones técnicas |
| 📖 **Manual de usuario** | Guía de uso paso a paso para el personal |

---

## ⛔ Regla clave
Dos citas activas del mismo médico **no pueden solaparse** en el tiempo. Se garantiza en la capa de servicio **y** con una restricción a nivel de base de datos (detalle en *Modelo de datos*).

---
*Centro de Salud Diagnóstico · Maracay, Aragua · Atención con cita previa.*
