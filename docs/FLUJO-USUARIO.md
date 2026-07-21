# Flujo de Usuario — ERP Diagnóstico

Diagrama de flujo (flowchart) del recorrido del personal en el sistema, según su rol (alcance **MVP**). Se renderiza automáticamente en GitHub (Mermaid).

## Flujo general por rol

```mermaid
flowchart TD
    A([Inicio]) --> B[Pantalla de login]
    B --> C{¿Credenciales válidas?}
    C -- No --> B
    C -- Sí --> D{¿Rol del usuario?}

    %% ADMIN
    D -- ADMIN --> E[Panel de administración]
    E --> E1[Gestionar usuarios y accesos]
    E --> E2[Gestionar médicos y especialidades]
    E --> E3[Gestionar servicios]
    E --> E4[Definir disponibilidad de médicos]

    %% RECEPCIÓN
    D -- RECEPCIÓN --> F[Panel de recepción]
    F --> F1[Gestionar pacientes]
    F --> F2[Ver agenda / calendario]
    F --> G[Crear / editar cita]

    %% MÉDICO
    D -- MÉDICO --> H[Mi agenda]
    H --> H1[Ver mis citas del día]
    H --> H2[Marcar atendida / no asistió]
    H --> H3[Cancelar una cita]

    %% Cierre
    E --> Z([Cerrar sesión])
    F --> Z
    H --> Z
```

> Recepción **no** ve gestión de usuarios, configuración ni reportes.

## Subflujo: crear una cita (upsert de paciente + cero solapamientos)

```mermaid
flowchart TD
    S([Nueva cita]) --> R[Elegir médico y servicio]
    R --> R1[Duración = la que elige recepción]
    R1 --> C1[Introducir paciente<br/>nombre completo + edad]
    C1 --> P{¿El paciente existe?}
    P -- No --> P1[Crear paciente<br/>rol PACIENTE]
    P1 --> T
    P -- Sí --> P2[Reutilizar paciente]
    P2 --> T[Elegir fecha y hora]
    T --> U{¿Dentro de la disponibilidad<br/>del médico?}
    U -- No --> Vov{¿Forzar cupo extra?<br/>sobrecupo}
    Vov -- No --> T
    Vov -- Sí --> W
    U -- Sí --> W{¿Se solapa con otra<br/>cita del médico?}
    W -- Sí --> X[Aviso: solapamiento · elige otra hora]
    X --> T
    W -- No --> Y[Guardar cita · SCHEDULED]
    Y --> Z([Cita agendada])
```

## Notas

- La validación (disponibilidad del médico + **cero solapamientos por médico**) y el **upsert de paciente** se ejecutan en la **capa de servicio** del backend (FastAPI) antes de guardar.
- El calendario **bloquea** (grisa) los días/horas fuera de la disponibilidad del médico; recepción puede **forzar un cupo extra** (sobrecupo) con confirmación.
- Los pacientes **no acceden** al sistema; toda gestión la realiza el personal.
- **Fase 2:** historia clínica (notas del médico), anti-solapamiento por recurso/sala, agrupar varios estudios (visita), recordatorios WhatsApp, auditoría y refuerzo con restricciones a nivel de base de datos.
