# Mapa de Componentes (React) — Atomic Design *lite*

> Inventario de componentes del **frontend** (repo `diagnostico-frontend`), derivado del `mockup/` y ceñido al **MVP**. Enfoque **Atomic Design ligero**: se usa la jerarquía como **guía de organización**, sin obsesionarse con clasificar cada pieza al milímetro.
>
> **🎯 Regla de oro: el código lo más sencillo posible.** Componentes pequeños y con **una sola responsabilidad**; nada de abstracciones prematuras ni librerías de estado complejas. Si algo se resuelve con `useState` + `fetch`, no metas más. Prima "que funcione y se lea claro" sobre "que sea sofisticado".

```
Átomos  →  Moléculas  →  Organismos  →  Plantillas  →  Páginas
(botón)    (campo)       (formulario)   (layout)       (ruta)
```

## Estructura de carpetas (repo frontend)

```
src/
  components/
    atoms/        # piezas básicas sin lógica de negocio
    molecules/    # combinaciones simples de átomos
    organisms/    # secciones completas con lógica/estado
  layouts/        # plantillas (AppLayout, AuthLayout)
  pages/          # una por ruta
  api/            # cliente HTTP + token JWT
  App.jsx         # rutas (React Router) + guardas por rol
```

## ⚛️ Átomos

| Componente | Uso |
|-----------|-----|
| `Boton` | variantes: primario · secundario · peligro |
| `Input` | texto · fecha · hora · número |
| `Select` | desplegables (médico, servicio, rol…) |
| `Label` | etiqueta de campo |
| `Badge` | pastilla de color (estado de cita, rol, activo/inactivo) |
| `Avatar` | iniciales del usuario/paciente |
| `Icono` | SVG (nav, acciones) |
| `Spinner` | estado de carga |

## 🧬 Moléculas

| Componente | Compuesto por | Uso |
|-----------|---------------|-----|
| `CampoFormulario` | Label + Input (+ error) | todos los formularios |
| `BarraBusqueda` | Input + Icono | buscar paciente/cédula |
| `EnlaceNav` | Icono + texto (+ activo) | sidebar |
| `TarjetaKPI` | título + número + delta | panel |
| `SelectorVista` | toggle Día / Semana | agenda |
| `FranjaHoraria` | día + hora inicio/fin | disponibilidad del médico |
| `ItemNota` | fecha + médico + texto | historia clínica (**fase 2, fuera del MVP**) |

## 🦠 Organismos

| Componente | Qué hace |
|-----------|----------|
| `Sidebar` | navegación por rol + usuario + salir |
| `Topbar` | título + búsqueda + botón "Nueva cita" |
| `PanelResumen` | fila de `TarjetaKPI` + agenda del día |
| `Calendario` | grid médico × hora; **grisa lo no disponible** y permite **sobrecupo** |
| `FormularioCita` | **upsert de paciente** + servicio/médico + fecha/hora + aviso de solapamiento |
| `TablaPacientes` | listado + acción "ver ficha" |
| `FormularioPaciente` | alta/edición: **nombre completo + edad** (cédula opcional) |
| `TarjetaMedico` | avatar + **especialidades (N:M)** + servicios + disponibilidad |
| `FichaCabecera` | datos del paciente + alergias/antecedentes |
| `FichaTabs` | pestañas: Datos · Historial de citas (la pestaña **Historia clínica** llega en **fase 2**) |
| `ListaNotasClinicas` | notas de evolución (`ItemNota`) — **fase 2, fuera del MVP** |
| `TablaUsuarios` | usuarios del sistema (solo ADMIN) |
| `FormularioUsuario` | nuevo acceso: nombre + email + rol |

## 🖼️ Plantillas (layouts)

| Plantilla | Estructura |
|-----------|-----------|
| `AuthLayout` | contenedor centrado (solo Login) |
| `AppLayout` | `Sidebar` + `Topbar` + área de contenido (todas las páginas tras login) |

## 📄 Páginas (ruta · rol)

| Página | Ruta | Quién accede | Organismos que usa |
|--------|------|--------------|--------------------|
| `LoginPage` | `/login` | todos | (AuthLayout) |
| `PanelPage` | `/` | todos | `PanelResumen` |
| `AgendaPage` | `/agenda` | todos | `Calendario` (+ `FormularioCita`) |
| `PacientesPage` | `/pacientes` | ADMIN · RECEPCION | `TablaPacientes` + `FormularioPaciente` |
| `FichaPacientePage` | `/pacientes/:id` | ADMIN · RECEPCION · MEDICO | `FichaCabecera` + `FichaTabs` (`ListaNotasClinicas` → **fase 2**) |
| `MedicosPage` | `/medicos` | ADMIN · RECEPCION | `TarjetaMedico` (grid) |
| `UsuariosPage` | `/usuarios` | **solo ADMIN** | `TablaUsuarios` + `FormularioUsuario` |
| `ConfiguracionPage` | `/config` | **solo ADMIN** | formularios de centro/servicios |

> **Guardas por rol** (en `App.jsx`): RECEPCIÓN **no** ve `/usuarios` ni `/config`; MEDICO ve su agenda (**solo lectura**). Las notas clínicas en la ficha del paciente llegan en **fase 2**.

## 🔑 Comportamientos clave (dónde vive la lógica)

- **`FormularioCita`** → al guardar: **upsert de paciente** por `nombre completo + edad` (si hay varios, se elige); el backend valida **disponibilidad** (con opción de **sobrecupo**) y **cero solapamientos por médico**.
- **`Calendario`** → pide al backend la disponibilidad del médico y **desactiva** los días/horas fuera de ella; recepción puede **forzar un cupo extra**.
- **`Badge`** de estado → mapea `EstadoCita` (SCHEDULED · CONFIRMED · CANCELLED · COMPLETED · NO_SHOW) a color.
- La **cédula** no se pide al agendar (opcional, se añade después).

> Este mapa es una **guía**, no un contrato rígido: si al codear una pieza encaja mejor en otro nivel, se mueve sin drama. Lo importante es no meter toda la UI en un solo archivo.
