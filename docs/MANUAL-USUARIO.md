# Manual de Usuario — ERP Diagnóstico

Guía de uso del sistema para el personal del centro. La interfaz está en español.

> Nota: las pantallas de referencia están en el prototipo visual (`mockup/index.html`).

## 1. Iniciar sesión

1. Abre la aplicación en el navegador.
2. Introduce tu **correo** y **contraseña**.
3. Pulsa **Entrar**. Verás un panel distinto según tu rol.

> Si es tu primer acceso, el sistema puede pedirte cambiar la contraseña.

## 2. El panel según tu rol

- **Administrador:** acceso a todo — usuarios, médicos, especialidades, servicios y duraciones, **consultorios/salas**, reportes y auditoría.
- **Recepción:** pacientes, agenda, citas/visitas y recordatorios.
- **Médico:** tu agenda, tus citas y la historia clínica.

## 3. Agendar una cita o visita (Recepción / Admin)

1. Pulsa **Nueva cita** (botón superior).
2. **Paciente:** búscalo por nombre o cédula. Si no existe, pulsa **Nuevo paciente** y regístralo.
3. **Servicio, médico y consultorio:** elige el servicio (consulta o estudio), el médico y el **consultorio/sala** donde se realiza. La **duración se calcula sola** según el médico + servicio.
4. **Varios estudios el mismo día (visita):** añade más servicios para ese día (ej. eco 9:00 + ecocardiograma 9:30 + holter 10:00). Se agendan juntos como una **visita**.
5. **Fecha y hora:** elige un hueco dentro de la disponibilidad del médico. Si el médico **o el consultorio/sala** ya están ocupados, el sistema **avisa** y no deja guardar; elige otro horario.
6. **Holter / MAPA:** el sistema te pide también la cita de **retiro** (normalmente al día siguiente).
7. Pulsa **Guardar**. El **recordatorio** de confirmación se programa automáticamente.

## 4. Editar, mover o cancelar una cita

1. Abre la cita desde la **agenda** o el **calendario**.
2. Cambia los datos (fecha, hora, tipo…) o pulsa **Cancelar cita**.
3. Al mover una cita, se vuelve a validar que no haya solapamiento.

## 5. Gestionar pacientes (Recepción / Admin)

1. Entra en **Pacientes**.
2. **Nuevo paciente:** rellena nombre, **cédula** (única; **opcional** si no tiene, p. ej. niños o extranjeros), fecha de nacimiento y teléfono.
3. Desde la **ficha** del paciente puedes ver su historial de citas y su historia clínica.

## 6. Gestionar médicos y servicios (Admin)

1. Entra en **Médicos**.
2. Da de alta un médico con su nombre, matrícula y **una o varias especialidades**.
3. Define los **servicios** que ofrece y la **duración** de cada uno (ej. consulta 45 min, ecocardiograma 30 min).
4. Define su **disponibilidad** (días y horas de atención).

> Los **consultorios, salas y equipos** (p. ej. ecógrafo, endoscopio) se gestionan también desde administración; al agendar se asigna uno y el sistema evita que dos citas usen el mismo a la vez.

## 7. Crear accesos para el personal (Admin)

1. Entra en **Usuarios**.
2. Pulsa **Nuevo acceso**: nombre, correo y **rol** (Administrador / Recepción / Médico).
3. Comparte la contraseña temporal con la persona; la cambiará al entrar.
4. Para dar de baja a alguien, márcalo como **inactivo** (no se borra, se conserva el historial).

## 8. Ver mi agenda y marcar asistencia (Médico)

1. Entra en **Mi agenda**.
2. Consulta tus citas del día.
3. Marca cada cita como **Atendida** o **No asistió** según corresponda.

## 9. Historia clínica (Médico)

1. Desde una cita o la **ficha del paciente**, entra en **Historia clínica**.
2. Consulta las **notas anteriores** (útil en reconsultas o si el paciente viene de otro especialista del área).
3. Pulsa **Nueva nota** para registrar la evolución de la visita de hoy.

## 10. Recordatorios de confirmación

- El sistema **envía solo** por WhatsApp la confirmación de la cita **24 h antes**.
- En el panel ves quién **confirmó**, quién no, y puedes **reenviar** si hace falta.

## 11. Sin conexión a internet

- Podrás **consultar** la agenda ya cargada aunque se caiga el internet.
- Para **crear o editar** citas necesitas conexión; el sistema te avisará si estás sin conexión.

## 12. Cerrar sesión

Pulsa tu nombre (abajo a la izquierda) → **Salir**. Cierra siempre la sesión en equipos compartidos.
