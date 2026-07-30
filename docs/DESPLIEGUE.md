# Despliegue — ERP Diagnóstico (backend)

El backend se despliega en **dos proveedores**: la **API** (FastAPI) como Web Service en
**Render**, configurada en `render.yaml` (Blueprint), y la **base de datos PostgreSQL** en
**Neon**, cuyo plan gratuito no caduca. La conexión a Neon se pega a mano en el panel de Render;
no se versiona.

> 🌐 **API en producción:** **https://diagnostico-api-jtbw.onrender.com** · Swagger en [`/docs`](https://diagnostico-api-jtbw.onrender.com/docs) · salud en [`/health`](https://diagnostico-api-jtbw.onrender.com/health).
> *(Ojo: el subdominio lleva sufijo `-jtbw` porque `diagnostico-api.onrender.com` estaba ocupado por otro servicio ajeno.)*

## Pasos (una sola vez)

1. Crear cuenta en **[render.com](https://render.com)** (login con GitHub).
2. En el panel: **New → Blueprint**.
3. Conectar el repositorio `diagnostico-backend` y elegir la rama.
4. Render detecta `render.yaml` y muestra lo que va a crear (solo la API; la base está en Neon).
5. Cuando lo pida, escribir los valores de **`DATABASE_URL`** (la cadena de Neon), de
   **`ADMIN_PASSWORD`** (la contraseña del admin) y de **`FRONTEND_ORIGINS`** (ver más abajo).
6. **Apply / Create** → Render aplica las migraciones sobre Neon, carga el seed y arranca la API.
7. Probar la **URL pública** (la actual: `https://diagnostico-api-jtbw.onrender.com`):
   - `GET /health` → `{"status":"ok","database":"ok"}` (un `503` con `"database":"unreachable"`
     significa que el servidor está vivo pero no alcanza la base)
   - `GET /docs` → la documentación Swagger
   - `POST /auth/login` con `admin@diagnostico.com` y la contraseña que pusiste.

## Qué hace Render automáticamente (según `render.yaml`)

- **Base de datos:** **ninguna** — Render ya no crea Postgres; se conecta al de Neon a través de
  `DATABASE_URL`, que se pega a mano en el panel.
- **Build:** `pip install` + `alembic upgrade head` (crea las tablas) + `python -m app.seed` (datos base).
- **Arranque:** `uvicorn` en el puerto que Render asigna (`$PORT`).
- **Secretos:** `JWT_SECRET` lo genera Render; `DATABASE_URL`, `ADMIN_PASSWORD` y
  `FRONTEND_ORIGINS` los pones tú.

## CORS: quién puede llamar a la API

El navegador solo deja que el frontend llame a la API si la API declara ese origen como
autorizado. La variable **`FRONTEND_ORIGINS`** admite **varios orígenes separados por comas**,
para que convivan el entorno local y el desplegado. Valor en producción:

```
FRONTEND_ORIGINS=http://localhost:5173,https://erp-diagnostico.vercel.app
```

> **El frontend está desplegado en Vercel**, en `https://erp-diagnostico.vercel.app`, y llama a
> esta API directamente (su `vercel.json` solo reescribe rutas de la SPA, no hace de proxy). Por
> eso su origen **tiene que** estar en esta lista.
>
> **Del otro lado**, el frontend necesita `VITE_API_URL=https://diagnostico-api-jtbw.onrender.com`
> en las variables de Vercel. Vite **incrusta esa variable en el build**, así que cambiarla exige
> **volver a desplegar el frontend**; no basta con guardarla.
>
> Las **previews de Vercel** (una URL distinta por rama) **no** están en la lista y el navegador
> las bloqueará. Es esperado: solo el dominio de producción habla con la API.

- **Sin barra final** y con el esquema incluido (`https://`): el origen se compara tal cual.
- Si la variable no está definida, se usa `http://localhost:5173`. Es decir, **si se despliega el
  frontend y no se define esta variable, el navegador bloqueará sus llamadas**.
- Por compatibilidad se sigue aceptando el nombre antiguo `FRONTEND_ORIGIN` (un solo origen).

## Migración de la base de datos a Neon (mejora `A7`)

**Por qué.** El PostgreSQL **gratuito de Render expira a los 30 días** de crearse y se **borra**
tras 14 días de gracia. El plan gratuito de **Neon es permanente** (0,5 GB de almacenamiento y
100 horas de cómputo por proyecto y mes). El **servicio web se queda en Render**, que sí es
gratis indefinidamente: solo se duerme a los 15 minutos sin tráfico.

> **Datos.** Mientras el sistema no esté entregado al cliente, en producción solo hay lo que crea
> el *seed* y las pruebas propias, así que **no hace falta volcar ni restaurar nada**: se crea la
> base nueva y se deja que las migraciones y el *seed* la llenen. En cuanto el centro empiece a
> registrar citas reales, esto deja de ser cierto y hará falta `pg_dump` antes de tocar nada
> (ver la mejora `A17` en [`MEJORAS-Y-PROXIMOS-PASOS.md`](MEJORAS-Y-PROXIMOS-PASOS.md)).

### Pasos

1. **Crear el proyecto en Neon** (región más cercana, PostgreSQL 16) y copiar su cadena de
   conexión.
2. **Comprobar la extensión `btree_gist`** desde el editor SQL de Neon, **antes** de migrar:

   ```sql
   CREATE EXTENSION IF NOT EXISTS btree_gist;
   ```

   La migración `3adfaea5a43a` (restricción anti-solapamiento) la necesita. Si este paso falla,
   `alembic upgrade head` se quedará a medias.
3. **Adaptar la cadena** al driver del proyecto y a los requisitos de Neon:

   ```
   postgresql+psycopg2://USUARIO:CLAVE@HOST.neon.tech/BASE?sslmode=require&channel_binding=require
   ```

   Neon **exige SSL**: sin `sslmode=require` no conecta.
4. **Probar en local antes de tocar producción**: poner esa cadena en el `.env` local y ejecutar

   ```bash
   alembic upgrade head
   python -m app.seed
   pytest
   ```

   Si los tests pasan contra Neon, el resto es configuración.
5. **Ajustar `render.yaml`**: quitar el bloque `databases:` (deja de crearse el Postgres de
   Render) y cambiar `DATABASE_URL` de `fromDatabase:` a `sync: false`, para pegarla a mano.
6. **En el panel de Render**, poner el valor de `DATABASE_URL` (la cadena de Neon) y comprobar
   que `ADMIN_PASSWORD` y `FRONTEND_ORIGINS` siguen definidos.
7. **Desplegar** (merge a `main` con su *tag*) y verificar en este orden: `GET /health`,
   `GET /docs` y un `POST /auth/login` con `admin@diagnostico.com`.
8. **No borrar la base vieja de Render hasta haber verificado el login** contra la nueva. Es la
   única vuelta atrás. Una vez verificada, se puede dejar que caduque.

### Ya resuelto en el código

- **Conexiones caídas:** Neon **suspende el cómputo** cuando nadie usa la base, y las conexiones
  guardadas en el pool mueren con ella. `app/db.py` crea el *engine* con `pool_pre_ping=True`,
  que comprueba que la conexión sigue viva antes de entregarla; sin eso, la primera petición tras
  la suspensión falla con `SSL SYSCALL error: EOF detected`.
- **Dependencias fijadas:** `requirements.txt` lleva versiones exactas, así que el despliegue no
  puede romperse por una actualización ajena justo el día de la migración.

## Copias de seguridad

> ⚠️ **Estado: montado pero SIN VERIFICAR de punta a punta.** Falta instalar PostgreSQL 18,
> elegir dónde se guardan los volcados y **probar una restauración**. Hasta que eso se haga, la
> única protección real es la capa 1.

Dos capas, porque cubren cosas distintas:

| Capa | Qué cubre | Qué **no** cubre |
|------|-----------|------------------|
| **1. Instant restore de Neon** | Rebobinar la base a cualquier momento de las **últimas 6 horas** (plan gratuito, hasta 1 GB de historial). Automático, no hay que hacer nada | Nada anterior a 6 horas. Ni perder el acceso al proyecto |
| **2. Volcado con `pg_dump`** | Todo lo demás: un borrado detectado al día siguiente, o quedarse sin cuenta de Neon | Lo que pase entre dos volcados |

### Capa 1 — Instant restore (ya activa)

En la consola de Neon, en el proyecto → **Restore**, se elige una marca de tiempo dentro de la
ventana de 6 horas. Es lo más rápido para un "he borrado algo hace un rato": no hace falta
volcado ni restauración manual.

### Capa 2 — Volcado periódico

**Requisito:** las *client tools* de **PostgreSQL 18**. `pg_dump` se niega a volcar de un servidor
más nuevo que él, y Neon corre PostgreSQL 18.4. El script lo comprueba y aborta con un mensaje
claro antes de intentar conectarse.

```powershell
$env:BACKUP_DATABASE_URL = "postgresql://usuario:clave@host.neon.tech/neondb?sslmode=require"
.\scripts\backup.ps1 -Destination "RUTA\A\ELEGIR"
```

Qué hace `scripts/backup.ps1`:

1. Comprueba que hay cadena de conexión y que `pg_dump` es la versión 18 o superior.
2. Vuelca en formato comprimido (`--format=custom`), con nombre `diagnostico-AAAAMMDD-HHmm.dump`.
3. **Comprueba que el volcado se puede leer** (`pg_restore --list`). Si no, lo borra y falla: un
   archivo corrupto que parece una copia es peor que no tener copia.
4. Conserva los últimos 14 y borra los anteriores.

La cadena de conexión se pasa por **variable de entorno**, no por parámetro ni en un archivo, para
que no acabe escrita en el historial de la consola ni en la tarea programada.

### Dónde guardarlos — decisión pendiente

**Nunca dentro del repositorio: es público.** Un volcado contiene nombres, cédulas y teléfonos de
pacientes; subirlo a GitHub sería publicarlos. Por lo mismo quedan descartados los artefactos de
GitHub Actions, que en un repo público puede descargar cualquiera.

El `.gitignore` bloquea `*.dump`, `*.sql.gz` y `backups/` para que no pueda colarse por accidente,
pero eso es una red, no la decisión.

La opción razonable es una **carpeta sincronizada con un disco en la nube** (OneDrive, Drive), que
saca la copia de la máquina sin coste. Está **por decidir**.

### Restaurar

```powershell
pg_restore --clean --if-exists --no-owner -d "postgresql://usuario:clave@host/base" archivo.dump
```

**Hay que probarlo al menos una vez**, y no contra producción: se crea una base nueva (o una rama
en Neon), se restaura ahí y se comprueba que los datos están. Una copia que nunca se ha restaurado
no se sabe si sirve.

### Cada cuánto

Mientras el volumen sea el actual (~60 citas/día), **una vez al día** es razonable: en el peor caso
se pierde un día de agenda, y las 6 horas de Neon cubren lo reciente. Se automatiza con el
**Programador de tareas** de Windows llamando al script.

## Notas

- Límites concretos del plan **gratuito** de Render: el servicio web **se duerme a los 15 minutos**
  sin tráfico y arranca con la siguiente petición (el primer acceso tarda), con **750 horas de
  instancia** al mes por *workspace*; y la base de datos **expira a los 30 días** de crearse, con
  14 días de gracia antes de borrarse — de ahí la migración a Neon descrita arriba.
- Cada `git push` a la rama desplegada vuelve a desplegar (migraciones incluidas).
