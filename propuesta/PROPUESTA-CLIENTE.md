# Sistema de Gestión de Citas y CRM Clínico — "Diagnóstico"

**Propuesta para presentación** · Julio 2026

Un software para gestionar de forma sencilla las **citas, los pacientes y las historias clínicas** del centro de salud, con acceso desde el ordenador y desde el móvil.

---

## 1. ¿Qué incluye el sistema?

| Apartado | Para qué sirve |
|----------|----------------|
| **Inicio de sesión** | Acceso seguro solo para el personal autorizado, con distintos niveles de permiso. |
| **Panel** | Vista rápida del día: citas de hoy, confirmadas, ocupación de la agenda e indicadores. |
| **Agenda** | Calendario semanal con todas las citas por médico. |
| **Pacientes** | Listado de pacientes con búsqueda por cédula, nombre o teléfono. |
| **Ficha de paciente** | Datos personales, historial de citas e **historia clínica** (alergias, antecedentes, medicación y notas de evolución). |
| **Médicos** | Profesionales del centro y sus especialidades. |
| **Reportes** | Estadísticas: citas por especialidad, tasa de asistencia, nuevos pacientes. |
| **Facturación** | Registro de facturas y estado de pago. |
| **Usuarios** | Gestión de los accesos del personal (administrador, recepción, médico). |
| **Configuración** | Datos del centro, tipos de consulta, respaldos e **integraciones** (Google Calendar, WhatsApp). |

### Punto destacado: control de horarios
El sistema **impide agendar dos citas que se solapen** con el mismo médico. Si intentas poner una cita en un horario ocupado, avisa automáticamente. Así no hay errores de agenda.

---

## 2. Niveles de acceso del personal

- **Administrador** — control total: usuarios, configuración, reportes.
- **Recepción** — gestiona pacientes y citas.
- **Médico** — ve su propia agenda y las historias de sus pacientes.

---

## 3. Integraciones

- **Google Calendar** — las citas aparecen en el calendario del móvil del médico o de recepción, para verlas en cualquier momento (sin mostrar datos clínicos, solo la hora y el paciente).
- **Recordatorios por WhatsApp** — aviso automático al paciente antes de su cita, para **reducir las inasistencias**.
- **Notificaciones por correo** — confirmaciones y recordatorios por email.

---

## 4. ¿Qué funciona sin internet?

El centro está en una zona donde el internet puede fallar, así que es importante saberlo:

**✅ Sin internet se puede CONSULTAR la información:**
- Ver la agenda del día y las citas
- Ver la ficha de un paciente y su historia clínica
- Revisar reportes ya cargados

**❌ Sin internet NO se pueden GUARDAR cambios:**
- Crear, mover o cancelar una cita
- Registrar un paciente nuevo o una nota clínica
- Emitir facturas

**❌ Necesitan internet siempre (dependen de servicios externos):**
- Ver las citas en Google Calendar
- Enviar recordatorios por WhatsApp o correo

> **En una frase:** sin internet puedes **ver** toda la información; para **guardar** cambios nuevos hace falta conexión.

---

## 5. Preguntas para afinar el proyecto

Para adaptar el sistema al centro, nos ayudaría conocer:

**Sobre el día a día**
1. ¿Cuántas citas se manejan al día, aproximadamente?
2. ¿Quién agenda las citas: solo recepción, o también los médicos?
3. ¿Cuántos médicos y qué especialidades hay?
4. ¿Qué tipos de consulta existen y cuánto dura cada uno (ej. primera visita, revisión)?

**Sobre el internet**
5. ¿Con qué frecuencia se cae el internet y cuánto suele durar?
6. Si se cae, ¿es aceptable **poder consultar pero no crear citas** hasta que vuelva? ¿O es imprescindible poder crear citas también sin conexión?
7. ¿Alguien necesita entrar al sistema **desde fuera del centro** (casa, móvil)?

**Sobre las funciones**
8. ¿Se necesita la **historia clínica** completa, o basta con datos básicos del paciente?
9. ¿Hace falta **facturación** dentro del sistema, o se lleva aparte?
10. ¿Interesan los **recordatorios por WhatsApp** a los pacientes?
11. ¿Quieren ver las citas en **Google Calendar** en el móvil?

**Sobre los datos y la puesta en marcha**
12. ¿Ya tienen pacientes registrados en algún sitio (Excel, papel, otro programa) que haya que pasar al sistema?
13. ¿Tienen logo, colores o nombre exacto del centro para personalizar la apariencia?

---

## 6. Próximos pasos

1. Revisar juntos esta propuesta y el boceto visual.
2. Responder las preguntas para cerrar el alcance de la primera versión.
3. Definir qué funciones entran en la **versión inicial** y cuáles quedan para más adelante.
4. Comenzar el desarrollo.

---

*Este documento acompaña al boceto visual (prototipo navegable). El boceto muestra el aspecto y la navegación; los datos que aparecen en él son de ejemplo.*
