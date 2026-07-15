# Manual de Usuario — ERP Diagnóstico

Guía de uso del sistema para el personal del centro (alcance **MVP**). La interfaz está en español.

> Nota: las pantallas de referencia están en el prototipo visual (`mockup/index.html`).

## 1. Iniciar sesión

1. Abre la aplicación en el navegador.
2. Introduce tu **correo** y **contraseña**.
3. Pulsa **Entrar**. Verás un panel distinto según tu rol.

## 2. El panel según tu rol

- **Administrador:** acceso a todo — usuarios, médicos, especialidades y servicios (con duraciones).
- **Recepción:** pacientes, agenda y citas. **No** ve usuarios, configuración ni reportes.
- **Médico:** tu agenda, tus citas y la historia clínica.

## 3. Agendar una cita (Recepción / Admin)

1. Pulsa **Nueva cita** (botón superior).
2. **Médico y servicio:** elige el médico y el servicio (consulta o estudio). La **duración se calcula sola** según el servicio.
3. **Paciente:** escribe su **cédula** (o nombre + fecha de nacimiento). Si ya existe, el sistema lo **detecta**; si no, lo **crea** automáticamente al guardar.
4. **Fecha y hora:** el calendario muestra solo los **días/horas disponibles** del médico. Si el médico ya está ocupado a esa hora, el sistema **avisa** y no deja guardar; elige otro hueco.
5. Pulsa **Guardar**. La cita queda como **agendada**.

## 4. Editar, mover o cancelar una cita

1. Abre la cita desde la **agenda** o el **calendario**.
2. Cambia los datos (fecha, hora, servicio…) o pulsa **Cancelar cita**.
3. Al mover una cita, se vuelve a validar que no haya solapamiento. Al **cancelar**, su hueco queda libre.

## 5. Gestionar pacientes (Recepción / Admin)

1. Entra en **Pacientes**.
2. **Nuevo paciente:** rellena nombre, **cédula** (única; **opcional** si no tiene, p. ej. niños o extranjeros), fecha de nacimiento y teléfono.
3. Desde la **ficha** del paciente puedes ver su historial de citas y su historia clínica.

## 6. Gestionar médicos y servicios (Admin)

1. Entra en **Médicos**.
2. Da de alta un médico con su nombre, matrícula y **una o varias especialidades**.
3. Define su **disponibilidad** (días y horas de atención).
4. En **Servicios**, define cada servicio y su **duración** (ej. consulta 45 min, ecocardiograma 30 min).

## 7. Crear accesos para el personal (Admin)

1. Entra en **Usuarios**.
2. Pulsa **Nuevo acceso**: nombre, correo y **rol** (Administrador / Recepción / Médico).
3. Comparte la contraseña con la persona.
4. Para dar de baja a alguien, márcalo como **inactivo** (no se borra, se conserva el historial).

## 8. Ver mi agenda y marcar asistencia (Médico)

1. Entra en **Mi agenda**.
2. Consulta tus citas del día.
3. Marca cada cita como **Atendida** o **No asistió** según corresponda.

## 9. Historia clínica (Médico)

1. Desde una cita o la **ficha del paciente**, entra en **Historia clínica**.
2. Consulta las **notas anteriores**.
3. Pulsa **Nueva nota** para registrar la evolución de hoy.

## 10. Cerrar sesión

Pulsa tu nombre (abajo a la izquierda) → **Salir**. Cierra siempre la sesión en equipos compartidos.

---

> **Fase 2 (próximas versiones):** agrupar varios estudios en un paso (visita), consultorios/salas y equipos, Holter/MAPA con retiro, recordatorios automáticos por WhatsApp, reportes y consulta offline.
