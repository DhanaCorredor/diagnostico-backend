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
para que convivan el entorno local y el desplegado:

```
FRONTEND_ORIGINS=http://localhost:5173,https://mi-frontend.onrender.com
```

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

## Notas

- Límites concretos del plan **gratuito** de Render: el servicio web **se duerme a los 15 minutos**
  sin tráfico y arranca con la siguiente petición (el primer acceso tarda), con **750 horas de
  instancia** al mes por *workspace*; y la base de datos **expira a los 30 días** de crearse, con
  14 días de gracia antes de borrarse — de ahí la migración a Neon descrita arriba.
- Cada `git push` a la rama desplegada vuelve a desplegar (migraciones incluidas).
