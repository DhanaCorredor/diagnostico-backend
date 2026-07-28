# Despliegue — ERP Diagnóstico (backend)

El backend se despliega en **Render** (un solo proveedor): el Web Service de la API
**y** su base de datos PostgreSQL. La configuración está en `render.yaml` (Blueprint).

> 🌐 **API en producción:** **https://diagnostico-api-jtbw.onrender.com** · Swagger en [`/docs`](https://diagnostico-api-jtbw.onrender.com/docs) · salud en [`/health`](https://diagnostico-api-jtbw.onrender.com/health).
> *(Ojo: el subdominio lleva sufijo `-jtbw` porque `diagnostico-api.onrender.com` estaba ocupado por otro servicio ajeno.)*

## Pasos (una sola vez)

1. Crear cuenta en **[render.com](https://render.com)** (login con GitHub).
2. En el panel: **New → Blueprint**.
3. Conectar el repositorio `diagnostico-backend` y elegir la rama.
4. Render detecta `render.yaml` y muestra lo que va a crear (la API + la base).
5. Cuando lo pida, escribir el valor de **`ADMIN_PASSWORD`** (la contraseña del admin) y el de
   **`FRONTEND_ORIGINS`** (ver más abajo).
6. **Apply / Create** → Render crea la base, aplica las migraciones, carga el seed y arranca la API.
7. Probar la **URL pública** (la actual: `https://diagnostico-api-jtbw.onrender.com`):
   - `GET /health` → `{"status":"ok"}`
   - `GET /docs` → la documentación Swagger
   - `POST /auth/login` con `admin@diagnostico.com` y la contraseña que pusiste.

## Qué hace Render automáticamente (según `render.yaml`)

- **Base de datos:** crea un PostgreSQL gratis y enchufa su conexión en `DATABASE_URL`.
- **Build:** `pip install` + `alembic upgrade head` (crea las tablas) + `python -m app.seed` (datos base).
- **Arranque:** `uvicorn` en el puerto que Render asigna (`$PORT`).
- **Secretos:** `JWT_SECRET` lo genera Render; `ADMIN_PASSWORD` y `FRONTEND_ORIGINS` los pones tú.

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

## Notas

- El plan **gratuito** de la base de datos y del servicio tiene límites (el servicio
  "duerme" tras un rato de inactividad → el primer acceso tarda unos segundos; la base
  gratis caduca a las pocas semanas). Suficiente para el MVP y la presentación.
- Cada `git push` a la rama desplegada vuelve a desplegar (migraciones incluidas).
