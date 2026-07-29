# ERP Diagnóstico — Mejoras y Próximos Pasos

> El MVP cubre el **núcleo** (agendar citas con cero solapamientos, validación de disponibilidad,
> gestión de pacientes/médicos/servicios), está **probado** y **desplegado** en producción
> (release `v0.6.1`). Este documento es el **catálogo único** de lo que queda por hacer:
> deuda técnica, mejoras que afectan al contrato de la API y funcionalidades de fase 2.
> Revisado y contrastado contra el código el **28 jul 2026**.

## 1. Cómo leer este catálogo

Cada mejora lleva un **identificador estable** (`A1`, `C2`…) para poder citarla en ramas,
commits e *issues*, y tres etiquetas:

| Etiqueta | Significado |
|----------|-------------|
| **Bloque** | `A` deuda técnica del backend · `B` cambios que tocan el contrato de la API · `C` funcionalidad de fase 2 |
| **Coste** | `bajo` (una sesión) · `medio` (una o dos sesiones, con migración o tests nuevos) · `alto` (varias sesiones o servicios externos) |
| **Toca frontend** | Si es `sí`, el cambio **no** se puede hacer solo en este repo: hay que coordinarlo con `diagnostico-frontend` |

## 2. Plan priorizado

Orden propuesto. `A7` va primero porque **tiene fecha límite externa**; el resto son mejoras
de backend puro que no rompen la UI. Estado a **28 jul 2026**.

| Orden | ID | Mejora | Coste | Toca frontend | Estado |
|:-----:|:--:|--------|:-----:|:-------------:|:------:|
| previa | **A9** | Conexiones caídas con una base que se suspende | bajo | no | ✅ |
| previa | **A12** | Dependencias con versión fijada | bajo | no | ✅ |
| previa | **A13** | `/health` comprueba la base de datos | bajo | no | ✅ |
| previa | **A15** | Últimos identificadores en español | bajo | no | ✅ |
| 0 | **A7** | Migrar la base de datos a Neon | medio | no | ✅ |
| 1 | **A1** | Franjas de disponibilidad solapadas | bajo | no | ✅ |
| 2 | **A2** | CORS multi-origen | bajo | no | ✅ |
| 3 | **A6** | Integración continua (CI) | bajo | no | ✅ |
| 4 | **A3** | Anti-solapamiento a nivel de base de datos | medio | no | ✅ |
| 5 | **A8** | Código y configuración en inglés | bajo | no | ✅ |
| 6 | **C1** | Historia clínica (notas del médico) | medio | sí | ⬜ |
| 7 | **A4** | Unicidad insensible a mayúsculas y acentos | medio | no | ⬜ |
| 8 | **A5** | Identificación robusta del paciente | medio | sí | ⬜ |
| 9 | **B1** | Paginación de listados | medio | sí | ⬜ |
| — | **A14** | Índices en la base de datos | bajo | no | ⬜ |
| — | **A17** | Copias de seguridad de la base | medio | no | ⬜ |

> Todo lo marcado ✅ está **publicado en producción** con la release `v0.7.0` (29 jul 2026), ya
> sobre la base de datos definitiva en Neon.

El resto del catálogo (`B2`, `C2`–`C5`) queda **sin fecha**: son mejoras válidas pero de
coste alto o de valor menor frente al riesgo que introducen.

## 3. Contrato de la API — qué añade y qué cambia la fase 2

> Mismo formato y misma función que la checklist del MVP ([`ROADMAP.md`](ROADMAP.md) §3.1):
> **antes de dar por hecha cualquiera de estas mejoras, se coteja contra esta tabla.**
> `✅` implementado · `⬜` pendiente. Las mejoras `A1`–`A4` y `A6` **no** aparecen aquí porque no
> tocan el contrato: son validaciones, configuración o infraestructura.

**Endpoints nuevos**

| Endpoint | Acción | Rol | Mejora | Estado |
|----------|--------|-----|--------|:------:|
| `POST /pacientes/{id}/notas` | Escribir una nota clínica sobre el paciente | MEDICO | C1 | ⬜ |
| `GET /pacientes/{id}/notas` | Leer la historia clínica del paciente | MEDICO·ADMIN | C1 | ⬜ |
| `GET /reportes/citas` | Citas por médico, servicio y periodo | ADMIN | C2 | ⬜ |
| `GET /reportes/ausencias` | Tasa de `NO_SHOW` por médico y periodo | ADMIN | C2 | ⬜ |
| `GET /reportes/ocupacion` | Ocupación real frente a la disponibilidad declarada | ADMIN | C2 | ⬜ |
| `GET /citas/{id}/auditoria` | Historial de cambios de una cita | ADMIN | C3 | ⬜ |
| `GET /recursos` · `POST /recursos` · `PUT /recursos/{id}` | Catálogo de recursos (ecógrafo, consultorios) | ADMIN | C4 | ⬜ |

**Endpoints existentes que cambian**

| Endpoint | Cambio | Mejora | Estado |
|----------|--------|--------|:------:|
| `GET /pacientes` · `GET /usuarios` | Aceptan paginación y la respuesta pasa a llevar el total | B1 | ⬜ |
| `POST /citas` · `POST /pacientes` · `PUT /pacientes/{id}` | El paciente se identifica por `fecha_nacimiento` (y/o cédula) en vez de por `edad` | A5 | ⬜ |
| `POST /citas` · `PUT /citas/{id}` | Aceptan `recurso_id` y validan el solapamiento también por recurso | C4 | ⬜ |
| `GET /citas` | Devuelve el recurso asignado a cada cita | C4 | ⬜ |

**Decisiones de contrato pendientes**

- **Las notas clínicas deberían ser solo de escritura y lectura, sin `PUT` ni `DELETE`.** En un
  contexto sanitario la historia clínica es un registro **acumulativo**: una nota equivocada se
  corrige con otra nota, no borrando la anterior. Si se decide permitir corrección, que sea
  añadiendo una nota que anule a la anterior, nunca modificando el texto original.
- **Quién lee la historia clínica.** Arriba está propuesto `MEDICO·ADMIN`. Recepción queda fuera,
  por coherencia con el criterio del MVP (recepción no ve usuarios, configuración ni reportes) y
  porque es el dato más sensible del sistema.
- **Alcance de la lectura del médico:** ¿cualquier médico ve la historia completa, o solo las
  notas de los pacientes que ha atendido? Lo primero es más simple; lo segundo es más correcto en
  protección de datos.

## 4. Qué hay que hacer en el frontend

> El frontend vive en el **repo aparte** `diagnostico-frontend`, con su propio flujo de ramas.
> Regla de orden: **primero se despliega la mejora en el backend, después se hace la UI**. Si la
> pantalla sale antes, pide a la API algo que todavía no existe.
> Las mejoras `A1`–`A4`, `A6` y `B2` no generan trabajo de UI (o solo el que se indica abajo).

### 4.1 Pendiente hoy, sin esperar a ninguna mejora

- **Pantalla para definir la disponibilidad de un médico.** `POST /disponibilidad` está
  implementado y forma parte del contrato del MVP, pero la UI solo **lee** las franjas
  (`DoctorsPage.jsx` hace `GET /disponibilidad?medico_id=`). Hoy las franjas solo se pueden crear
  llamando a la API a mano o por el *seed*, así que el administrador no puede cambiar el horario
  de un médico desde la aplicación. Es el hueco más visible que queda en la UI.
  Al hacerla, hay que mostrar el `409` que ahora devuelve la mejora `A1` (franja cruzada) además
  del `400` de "inicio posterior al fin".

### 4.2 Trabajo derivado de cada mejora

| Mejora | Qué hay que hacer en `diagnostico-frontend` |
|--------|---------------------------------------------|
| **A5** · identificación del paciente | En el formulario de paciente y en el de cita, pedir **fecha de nacimiento** en vez de edad, y mostrar la edad calculada a partir de ella |
| **B1** · paginación | Paginador en las tablas de **Pacientes** y **Usuarios**, leyendo el total que pasa a devolver la API |
| **C1** · historia clínica | En la ficha del paciente, una sección de **notas clínicas**: lista de notas y formulario para escribir una nueva. Visible solo para `MEDICO` y `ADMIN`. Implica que el médico **deja de ser solo lectura**, así que hay que revisar las guardas de rol y el menú |
| **C2** · reportes | Sección nueva de **reportes**, solo para `ADMIN`: citas por médico/servicio/periodo, ausencias y ocupación |
| **C3** · auditoría | En el detalle de la cita, el **historial de cambios** (quién la creó, editó o canceló). Solo `ADMIN` |
| **C4** · recursos y salas | Selector de **recurso** en el formulario de cita, y mantenimiento del catálogo de recursos en la pantalla de configuración |

### 4.3 Ya hecho — no rehacer

- **Botón de baja del paciente:** implementado en `PatientsPage.jsx`, con modal de confirmación y
  aviso de que la baja es lógica y recuperable. Figuraba como pendiente en la versión anterior de
  este documento.

## 5. Bloque A — Deuda técnica del backend

### A1 · Franjas de disponibilidad solapadas · coste bajo

- **Hoy:** `create_availability()` ([`app/services/availability.py`](../app/services/availability.py))
  valida que el médico exista, que tenga rol `MEDICO` y que `hora_inicio < hora_fin`. **No**
  comprueba que la franja nueva choque con otra del mismo médico y el mismo día.
- **Consecuencia:** se puede guardar "lunes 08:00–12:00" y "lunes 10:00–14:00" para el mismo
  médico. La agenda deja de tener una sola verdad sobre cuándo trabaja.
- **Por qué importa:** el proyecto se sostiene sobre la promesa de *cero solapamientos*, y esta
  es la única puerta por la que entra un solapamiento sin control.
- **Qué haríamos:** una excepción nueva (`OverlappingSlot`) en la capa de servicio, comprobando
  contra las franjas existentes del médico ese día con la regla estándar de intersección
  (`inicio_nuevo < fin_existente` y `fin_nuevo > inicio_existente`); el controlador la traduce a
  `409`. Tests del caso solapado, del contiguo (08:00–12:00 y 12:00–16:00 **sí** debe permitirse)
  y del duplicado exacto.

### A2 · CORS multi-origen · coste bajo

- **Hoy:** [`app/main.py`](../app/main.py) lee `FRONTEND_ORIGIN` del entorno y lo pasa como una
  lista de **un solo elemento** a `CORSMiddleware`.
- **Consecuencia:** el mismo despliegue no puede atender a la vez al frontend local
  (`http://localhost:5173`) y al de producción; hay que cambiar la variable a mano.
- **Qué haríamos:** aceptar una lista separada por comas (`FRONTEND_ORIGINS`), normalizar los
  espacios y mantener el valor por defecto de desarrollo. Documentarlo en
  [`DESPLIEGUE.md`](DESPLIEGUE.md) y en `.env.example`.

### A3 · Anti-solapamiento a nivel de base de datos · coste medio

- **Hoy:** el solapamiento de citas por médico se impide en la capa de servicio
  (`has_overlap()` en [`app/services/appointments.py`](../app/services/appointments.py)), que es
  donde vive toda la regla de negocio.
- **Consecuencia:** si en el futuro se escribe en la tabla `citas` por otra vía (un script, una
  carga masiva, un segundo proceso concurrente), nada impide el solapamiento.
- **Qué haríamos:** una migración de Alembic que añada a `citas` una restricción
  `EXCLUDE USING gist` sobre `medico_id` y el rango `[starts_at, ends_at)`, limitada a las citas
  en estado activo, más la extensión `btree_gist`. Es una **red de seguridad**, no un sustituto:
  la validación de servicio se queda porque es la que produce mensajes de error entendibles.
- **Aviso:** la restricción es específica de PostgreSQL; hay que comprobar que los tests (que
  usan la misma base) siguen en verde.

### A4 · Unicidad insensible a mayúsculas y acentos · coste medio

- **Hoy:** las comprobaciones de duplicado comparan las cadenas tal cual
  (`value_in_use()` en [`app/services/common.py`](../app/services/common.py)).
- **Consecuencia:** `MARÍA PÉREZ`, `maria perez` y `María Perez` conviven como tres registros
  distintos. Con recepción escribiendo a mano, pasa.
- **Qué haríamos:** normalizar antes de comparar (minúsculas + sin acentos) para `email`,
  `nombre` de servicio/especialidad y `cédula`, y decidir si se guarda también una columna
  normalizada con índice único, o basta con la comprobación en la capa de servicio.

### A5 · Identificación robusta del paciente · coste medio

- **Hoy:** `find_or_create_patient()` ([`app/services/patients.py`](../app/services/patients.py))
  identifica al paciente por `nombre_completo` + `edad`.
- **Consecuencia:** `edad` es un dato que **cambia cada año**. El mismo paciente que vuelve al
  año siguiente no coincide y se crea duplicado. Es un problema del modelo de datos, no un
  detalle de implementación.
- **Qué haríamos:** apoyar la identificación en `fecha_nacimiento` (que ya existe en la tabla
  `usuarios`) y/o en la cédula, y derivar la edad en vez de almacenarla. Requiere migrar los
  datos existentes y ajustar el formulario del frontend → **toca frontend**.

### A6 · Integración continua (CI) · coste bajo

- **Hoy:** los tests se ejecutan a mano (`pytest`).
- **Qué haríamos:** un *workflow* de GitHub Actions que, en cada `push` y cada *pull request*,
  levante un PostgreSQL de servicio, instale las dependencias, aplique las migraciones y corra
  la suite; más el *badge* de estado en el `README`.
- **Por qué importa:** el flujo de ramas ya es parte del proyecto; la CI es lo que lo convierte
  en una garantía y no en una costumbre.

### A7 · Migrar la base de datos a Neon · coste medio · **hecha (29 jul 2026)**

> **Migración completada y verificada.** La API de producción corre sobre **Neon**
> (PostgreSQL 18.4, región `us-east-2`), publicada con la release `v0.7.0`. Se comprobó que
> producción usa realmente la base nueva comparando los **UUID** de los catálogos, que se generan
> al azar en cada siembra y por tanto difieren entre bases. Verificado además: `/health` con
> `"database":"ok"`, *login* correcto, CORS autorizando el frontend de Vercel y el *bundle* del
> frontend apuntando a la API de Render. La base antigua de Render (`diagnostico-db`) se puede
> dejar caducar. **La herramienta queda funcionando gratis y sin fecha de caducidad.**

- **Hoy:** producción usa el **PostgreSQL gratuito de Render** (`diagnostico-db`, definido en
  `render.yaml`, añadido el 15 jul 2026).
- **El problema:** en el plan gratuito de Render, una base de datos **expira a los 30 días de
  crearse** y se **borra** tras 14 días de gracia. Con la fecha del *blueprint* como referencia,
  eso son **~14 ago 2026** para la expiración y **~28 ago 2026** para el borrado. *(Pendiente de
  confirmar la fecha real de creación en el panel de Render.)* El servicio web, en cambio, **no**
  caduca: solo se duerme a los 15 minutos sin tráfico y arranca con la siguiente petición.
- **La solución:** mover la base de datos a **Neon**, cuyo plan gratuito es **permanente** (0,5 GB
  de almacenamiento y 100 horas de cómputo por proyecto y mes, de sobra para este ERP, que además
  se suspende solo cuando nadie lo usa). El servicio web se queda en Render, gratis.
- **Qué haríamos:** exportar los datos del Postgres de Render, crear el proyecto en Neon, cambiar
  `DATABASE_URL` en Render, comprobar que `alembic upgrade head` y el *seed* funcionan contra la
  base nueva, verificar el *login* en producción y documentarlo en [`DESPLIEGUE.md`](DESPLIEGUE.md).
- **Por qué está la primera:** es la única del catálogo cuya demora tiene consecuencias
  irreversibles — si caduca, se pierden los datos y el backend desplegado deja de responder.
- **Procedimiento paso a paso:** escrito en [`DESPLIEGUE.md`](DESPLIEGUE.md), sección
  *Migración de la base de datos a Neon*. Incluye dos cambios de configuración que forman parte
  de esta mejora y no tienen ficha propia: **quitar el bloque `databases:` de `render.yaml`** (si
  no, Render sigue creando y enchufando su propia base) y **añadir `sslmode=require` a la cadena
  de conexión** (Neon exige SSL).
- **Requisitos previos, ya resueltos:** `A9` (comprobar las conexiones del pool antes de usarlas)
  y `A12` (dependencias con versión fijada).

### A8 · Código y configuración en inglés · coste bajo · **hecha**

- **Antes:** los identificadores del código ya estaban en inglés, pero los **docstrings** y los
  comentarios de configuración seguían en español, así que el proyecto leía mezclado.
- **Qué se hizo:** 123 docstrings y comentarios traducidos a inglés en 46 archivos (`app/`,
  `tests/`, `.env.example`, `render.yaml`, `.github/workflows/ci.yml`). Como efecto secundario,
  **Swagger (`/docs`) pasa a describir los endpoints en inglés**.
- **Qué se dejó en español, a propósito:** los **mensajes de error de la API** (los lee el
  personal del centro a través de la interfaz), los **datos** del *seed* (nombres reales de
  especialidades, servicios y médicos), las etiquetas de Swagger y el título de la aplicación,
  que acompañan a las rutas en español del contrato.
- **De regalo:** se corrigieron dos referencias obsoletas que la documentación arrastraba
  (`GRID_MINUTOS` → `GRID_MINUTES` y `crear_cita` → `create_appointment`).

### A9 · Conexiones caídas con una base que se suspende · coste bajo · **hecha**

- **Antes:** `app/db.py` creaba el *engine* con `create_engine(DATABASE_URL)` a secas.
- **El problema:** una base gestionada que **se suspende cuando nadie la usa** (como Neon) mata
  las conexiones que SQLAlchemy guarda en el pool. Al despertar, la primera petición reutiliza una
  conexión muerta y falla con `SSL SYSCALL error: EOF detected`.
- **Qué se hizo:** `pool_pre_ping=True`, que comprueba que la conexión sigue viva antes de
  entregarla, más dos tests (`tests/test_db.py`). Es requisito para `A7`.

### A12 · Dependencias con versión fijada · coste bajo · **hecha**

- **Antes:** `requirements.txt` no fijaba ninguna versión, así que cada build de Render instalaba
  lo último publicado ese día y la CI podía estar usando versiones distintas de producción.
- **Qué se hizo:** versión exacta para las diez dependencias. El despliegue deja de poder romperse
  por una actualización ajena.

### A13 · `/health` comprueba la base de datos · coste bajo · **hecha**

- **Antes:** `/health` devolvía `{"status":"ok"}` con solo comprobar que el servidor respondía.
- **El problema:** con una base que se suspende sola, el servidor puede estar perfectamente vivo y
  la base inalcanzable, y el *health check* decía que todo iba bien.
- **Qué se hizo:** el endpoint ejecuta un `SELECT 1` y responde `{"status":"ok","database":"ok"}`;
  si la base no contesta, devuelve `503` con `"database":"unreachable"`. De paso pasó a `async`.

### A14 · Índices en la base de datos · coste bajo

- **Hoy:** no hay **ni un índice declarado** en los modelos ni creado en la migración inicial.
  Solo existen los implícitos de clave primaria y `UNIQUE`, más el `gist` de `A3`.
- **Dónde se notaría:** `GET /citas` filtra por rango de `starts_at`, y el *upsert* de paciente
  filtra por `rol` + `nombre_completo` + `edad` en **cada** cita que se agenda.
- **Con honestidad:** con ~60 citas al día las tablas son pequeñas y PostgreSQL las recorre
  enteras sin despeinarse, así que la mejora **no se va a notar en la práctica** a corto plazo.
  Es barata y correcta, pero no urgente.

### A15 · Últimos identificadores en español · coste bajo · **hecha**

Quedaban `ya_tiene` y dos variables de bucle `dia` en `app/seed.py`, del renombrado anterior.
Los nombres de columna (`dia_semana`) **no** se tocan: son contrato.

### A17 · Copias de seguridad de la base · coste medio · **condicionada**

- **Hoy no es urgente:** el sistema aún no se ha entregado al cliente, así que en producción solo
  hay datos del *seed* y pruebas propias. Se puede recrear la base desde cero sin perder nada.
- **Cuándo pasa a ser lo más importante del proyecto:** en cuanto el centro registre citas y
  pacientes reales. Un plan gratuito no trae copias automáticas, y son datos de salud.
- **Qué haría falta:** un volcado periódico (`pg_dump`) guardado fuera del proveedor, y —lo que
  más se olvida— **probar la restauración**, porque una copia que nunca se ha restaurado no se
  sabe si sirve.

## 6. Bloque B — Cambios que tocan el contrato de la API

> Ninguno se puede hacer solo en este repo: cambian lo que el frontend consume.

### B1 · Paginación de listados · coste medio

- **Hoy:** `GET /pacientes` y `GET /usuarios` devuelven **todos** los registros activos.
- **Consecuencia:** con ~60 citas al día el censo de pacientes crece rápido; la respuesta y la
  tabla del frontend crecen con él.
- **Qué haríamos:** parámetros `limit`/`offset` (o `page`/`size`) con valores por defecto
  sensatos y un envoltorio de respuesta con el total, para que la UI pueda paginar.

### B2 · Contrato de la API en inglés · coste alto · **no planificado**

- **Situación:** el **código** ya está íntegramente en inglés. Lo que sigue en español es el
  **contrato**: rutas (`/citas`, `/pacientes`…), campos JSON (`nombre_completo`, `medico_id`…),
  valores de enum y nombres de tablas y columnas.
- **Decisión:** se mantiene en español **a propósito**. Es el idioma del centro de salud y el de
  la interfaz, así que el contrato habla el lenguaje del dominio. Cambiarlo obliga a tocar a la
  vez backend, frontend y base de datos (migración de tablas y columnas) sin aportar nada
  funcional.
- **Si algún día se hace:** en un único paso coordinado entre los dos repos, con migración de
  Alembic para el renombrado de tablas y columnas, y despliegue simultáneo.

## 7. Bloque C — Fase 2, funcionalidades

Funcionalidad de valor que se dejó **conscientemente fuera** del MVP para cumplir el plazo.

### C1 · Historia clínica (notas del médico) · coste medio

- **Andamiaje ya hecho:** la tabla `notas_clinicas` existe
  ([`app/models/clinical_note.py`](../app/models/clinical_note.py)) con claves foráneas a
  paciente, médico y cita; y `usuarios` ya tiene las columnas `alergias` y `antecedentes`.
- **Qué falta:** los *schemas* Pydantic, el servicio, los endpoints
  (`POST`/`GET /pacientes/{id}/notas`) y **devolver al médico capacidad de escritura**, que hoy
  es de solo lectura por decisión de alcance del MVP (ver [`ROADMAP.md`](ROADMAP.md) §0).
- **Por qué va la primera de la fase 2:** es la que más base tiene construida y la que más se
  nota en una demostración.
- **Aviso:** al abrir la escritura al rol `MEDICO` hay que revisar las guardas de rol y la
  documentación de permisos, que hoy describen al médico como solo lectura.

### C2 · Reportes y estadísticas · coste medio

Citas por médico, por servicio y por periodo; tasa de ausencias (`NO_SHOW`); ocupación de la
agenda frente a la disponibilidad declarada. No requiere datos nuevos: todo se calcula con lo
que ya se guarda. Recepción **no** tiene acceso a reportes (ver `ROADMAP.md` §0).

### C3 · Auditoría / log de cambios · coste medio

- **Hoy:** la tabla `citas` guarda `creado_por_id`, `created_at` y `updated_at`, es decir, quién
  la creó y cuándo se tocó por última vez.
- **Qué falta:** el **historial**: quién editó, movió o canceló cada cita y cuándo. Sería una
  tabla de eventos aparte, escrita desde la capa de servicio.
- **Por qué importa:** es un ERP de un centro de salud; la trazabilidad de quién cambió una cita
  es una petición razonable de la dirección.

### C4 · Recursos y salas · coste alto

Hoy el anti-solapamiento es **solo por médico**. En el centro, el cuello de botella real son los
**recursos** (el ecógrafo, cada consultorio): dos médicos distintos pueden tener citas a la vez
que necesitan el mismo aparato. Implica una tabla de recursos, su asociación con los servicios y
extender la regla de solapamiento a esa dimensión.

### C5 · Resto de fase 2 · coste alto

| Mejora | Nota |
|--------|------|
| **Recordatorios por WhatsApp** | Aviso automático al paciente antes de la cita; depende de un proveedor externo |
| **Visitas (agrupar estudios)** | Varios estudios de un paciente en una misma visita |
| **Duración por médico/servicio** | Duraciones por defecto según el tipo de estudio o el médico (hoy la elige recepción) |
| **Holter: colocación y retiro** | Modelar un mismo estudio en dos momentos separados |
| **Portal de pacientes** | Que el paciente consulte o gestione sus propias citas; implica auth pública |
| **Integración con Google Calendar** | Sincronizar la agenda del médico |
| **PWA offline** | Uso básico sin conexión en recepción |

## 8. Fuera del sistema

**Facturación y cobros:** quedan fuera del ERP (SENIAT, pago directo). No es un pendiente, es una
decisión de alcance.

## 9. Ya resuelto

Se anota lo que estuvo en este documento como pendiente y hoy ya no lo está, para que no vuelva a
proponerse:

- **Despliegue de las mejoras** (filtro de servicios por especialidad N:M, baja lógica de
  pacientes y usuarios, código renombrado a inglés): publicado en producción con la release
  `v0.6.1`.
- **Convención de fechas:** la API trabaja en hora local *naive* y **rechaza fechas con zona
  horaria** (`422`); el "ahora" se calcula en hora del centro (UTC−4) para no descuadrar en un
  servidor que corre en UTC.

---

> Ver también: [`ROADMAP.md`](ROADMAP.md) (fases y planificación) · [`MODELO-DATOS.md`](MODELO-DATOS.md)
> (andamiaje de fase 2) · [`ARQUITECTURA.md`](ARQUITECTURA.md) (estructura y patrones).
