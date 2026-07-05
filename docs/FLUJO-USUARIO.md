# Flujo de Usuario — ERP Diagnóstico

Diagrama de flujo (flowchart) del recorrido del personal en el sistema, según su rol. Se renderiza automáticamente en GitHub (Mermaid).

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
    E --> E3[Gestionar servicios y duraciones]
    E --> E4[Ver reportes y auditoría]

    %% RECEPCIÓN
    D -- RECEPCIÓN --> F[Panel de recepción]
    F --> F1[Gestionar pacientes]
    F --> F2[Ver agenda / calendario]
    F --> G[Crear / editar cita]

    %% MÉDICO
    D -- MÉDICO --> H[Mi agenda]
    H --> H1[Ver mis citas del día]
    H --> H2[Marcar atendida / no asistió]

    %% Cierre
    E --> Z([Cerrar sesión])
    F --> Z
    H --> Z
```

## Subflujo: crear una cita / visita (regla de cero solapamientos)

```mermaid
flowchart TD
    S([Nueva cita / visita]) --> P{¿El paciente existe?}
    P -- No --> P1[Registrar paciente<br/>cédula opcional]
    P1 --> Q
    P -- Sí --> Q[Seleccionar paciente]
    Q --> R[Elegir servicio y médico]
    R --> R1[Duración = DoctorServicio<br/>médico + servicio]
    R1 --> T[Elegir fecha y hora]
    T --> U{¿Dentro de la disponibilidad<br/>del médico?}
    U -- No --> V[Aviso: fuera de horario]
    V --> T
    U -- Sí --> W{¿Se solapa con otra<br/>cita activa del médico?}
    W -- Sí --> X[Aviso: horario no disponible]
    X --> T
    W -- No --> M{¿Añadir otro estudio<br/>el mismo día?}
    M -- Sí --> R
    M -- No --> Y[Guardar visita y citas · SCHEDULED]
    Y --> Y1[Programar recordatorio WhatsApp]
    Y1 --> Y2[Registrar en auditoría]
    Y2 --> Z([Visita agendada])
```

## Notas

- La validación de solapamiento se ejecuta en la **capa de servicio** y se refuerza con una restricción a nivel de **base de datos** (ver `MODELO-DATOS.md`).
- Los pacientes **no acceden** al sistema; toda gestión la realiza el personal.
- Toda acción sobre datos médicos queda registrada en **auditoría** (requisito HIPAA/GDPR).
