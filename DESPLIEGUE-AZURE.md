# Guía de Despliegue en Azure — Paso a Paso desde Cero

**Para quién es esta guía:** alguien que nunca desplegó nada. Cada comando está
explicado. Tiempo estimado total: 2-4 horas la primera vez.

**Tu situación:** cuenta Azure for Students con ~$90 de crédito, Docker ya
instalado, y una cuenta estudiantil que **no permite crear recursos en
todas las regiones** (abajo te digo cómo manejarlo).

---

## 0. Conceptos básicos (léelo, son 2 minutos)

| Término | Qué es, en simple |
|---------|-------------------|
| **Imagen Docker** | Un "paquete congelado" con tu app + todo lo que necesita (Python, librerías). Se construye una vez y corre igual en cualquier máquina. |
| **Contenedor** | Una imagen *en ejecución*. |
| **Registry (ACR)** | Un "Google Drive de imágenes Docker". Subes tu imagen ahí y Azure la descarga para ejecutarla. |
| **App Service** | El servicio de Azure que ejecuta tu contenedor y le da una URL pública con HTTPS gratis (`https://tuapp.azurewebsites.net`). |
| **Grupo de recursos** | Una "carpeta" que agrupa todo lo que crees en Azure. Borras la carpeta → borras todo (útil para no gastar crédito). |

### Arquitectura final

```
   Celular (Flutter)          Navegador (Angular)
          │                            │
          ▼                            ▼
┌──────────────────────┐   ┌──────────────────────────┐
│  App Service BACKEND │   │  App Service FRONTEND    │
│  (contenedor FastAPI)│◄──│  (contenedor nginx)      │
│  api-auxilio....net  │   │  web-auxilio....net      │
└──────────┬───────────┘   └──────────────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Azure Database for          │
│ PostgreSQL (administrada)   │  ← la BD NO va en Docker en producción
└─────────────────────────────┘
```

### ¿La base de datos se dockeriza o no? — Respuesta directa

- **En tu máquina (pruebas):** SÍ — el `docker-compose.yml` que ya tienes
  levanta un PostgreSQL en contenedor para probar todo junto.
- **En Azure (producción): NO.** Un contenedor es desechable: si App Service
  lo reinicia (y lo hace), **perderías todos los datos**. Lo correcto es usar
  **Azure Database for PostgreSQL** (servicio administrado): datos
  persistentes, backups automáticos, sin configurar nada.

### Costos estimados con tus $90

| Recurso | Plan | Costo aprox./mes |
|---------|------|------------------|
| PostgreSQL Flexible Server | B1ms (burstable) + 32 GB | ~$13-16 |
| App Service Plan | B1 Linux (¡UNO solo para las DOS apps!) | ~$13 |
| Container Registry | Basic | ~$5 |
| **TOTAL** | | **~$31-34/mes → unos 2.5 meses de crédito** |

> 💡 Truco clave de ahorro: **un solo App Service Plan B1 puede hospedar
> las dos Web Apps** (backend y frontend). No pagues dos planes.
> Y cuando no estés usando el sistema (ej. después de la defensa),
> apaga o borra los recursos (sección 10).

---

## 1. Requisitos previos

```powershell
# a) Verificar Docker (ya lo tienes)
docker --version

# b) Instalar Azure CLI (la herramienta de comandos de Azure)
winget install Microsoft.AzureCLI
# Cierra y reabre PowerShell después de instalar

# c) Iniciar sesión en Azure (abre el navegador para loguearte)
az login
```

---

## 2. PARTE 1 — Dockerizar y probar en tu máquina

Ya están creados estos archivos (todos comentados por dentro):

| Archivo | Qué hace |
|---------|----------|
| `backend/Dockerfile` | Imagen del backend: Python 3.12 + requirements + tu código + uvicorn |
| `backend/.dockerignore` | Excluye venv, `.env` (los secretos NUNCA van dentro de la imagen) |
| `frontend/Dockerfile` | Build multi-etapa: Node compila Angular → nginx sirve los archivos |
| `frontend/nginx.conf` | Config de nginx con soporte para rutas de Angular y la PWA |
| `frontend/.dockerignore` | Excluye node_modules, dist |
| `docker-compose.yml` | Levanta BD + backend + frontend juntos para probar |

### Probar todo localmente

> ⚠️ Esto construye las imágenes la primera vez (~5-10 min) y usa ~2 GB de
> RAM con todo corriendo. Hazlo con la laptop descargada de otras cosas.

```powershell
cd D:\SI2Parcial1

# Construir y levantar TODO (BD + backend + frontend)
docker compose up --build

# Cuando termine de arrancar:
#   Backend  → http://localhost:8000/docs
#   Frontend → http://localhost:8080
#   (la BD del compose está vacía: puedes correr migraciones/seed contra
#    localhost:5434 si quieres datos, o solo verificar que /docs abre)

# Para apagar: Ctrl+C y luego
docker compose down
```

Si `http://localhost:8000/docs` y `http://localhost:8080` abren, la
dockerización funciona y estás listo para Azure.

---

## 3. PARTE 2 — Crear el grupo de recursos (y el tema de las regiones)

### Sobre tu cuenta estudiantil y las regiones

Las cuentas de estudiante tienen **cuota limitada por región**: algunas
regiones rechazarán la creación con errores tipo *"This subscription is
restricted..."* o *"quota exceeded"*. **No es tu culpa ni un error tuyo**:
simplemente prueba con otra región de esta lista (en este orden, suelen
funcionar con cuentas de estudiante):

1. `eastus2` 2. `westus2` 3. `centralus` 4. `eastus` 5. `northeurope` 6. `brazilsouth`

```powershell
# Crear el grupo de recursos (la "carpeta" de todo el proyecto)
# Si eastus2 te da error, repite cambiando --location por el siguiente de la lista
az group create --name rg-auxilio --location eastus2
```

> A partir de aquí usa SIEMPRE la misma región que te funcionó.
> En los comandos siguientes la escribo como `eastus2` — cámbiala si usaste otra.

---

## 4. PARTE 3 — Base de datos PostgreSQL en Azure

```powershell
# 1. Crear el servidor PostgreSQL (tarda 5-10 minutos)
#    ⚠️ CAMBIA la contraseña por una tuya (guárdala bien)
az postgres flexible-server create `
  --resource-group rg-auxilio `
  --name pg-auxilio-tunombre `
  --location eastus2 `
  --tier Burstable `
  --sku-name Standard_B1ms `
  --storage-size 32 `
  --version 16 `
  --admin-user adminpg `
  --admin-password "TuPasswordSegura123!" `
  --public-access 0.0.0.0
```

Notas:
- `pg-auxilio-tunombre`: el nombre debe ser ÚNICO en todo Azure — agrega tu nombre/apellido.
- `--public-access 0.0.0.0` activa la regla **"permitir servicios de Azure"**
  (para que App Service pueda conectarse) — no significa abierto al mundo.
- Si pregunta si quieres habilitar acceso para tu IP actual, dile que **sí**
  (lo necesitas para correr las migraciones desde tu laptop).

```powershell
# 2. Crear la base de datos dentro del servidor
az postgres flexible-server db create `
  --resource-group rg-auxilio `
  --server-name pg-auxilio-tunombre `
  --database-name db
```

### Tu cadena de conexión (apúntala)

```
postgresql://adminpg:TuPasswordSegura123!@pg-auxilio-tunombre.postgres.database.azure.com:5432/db?sslmode=require
```

> El `?sslmode=require` al final es **obligatorio** — Azure solo acepta
> conexiones cifradas. Sin eso verás errores de conexión.

### 3. Crear las tablas (migraciones) y datos desde tu laptop

```powershell
cd D:\SI2Parcial1\backend

# Apuntar temporalmente a la BD de Azure (solo en esta terminal)
$env:DATABASE_URL = "postgresql://adminpg:TuPasswordSegura123!@pg-auxilio-tunombre.postgres.database.azure.com:5432/db?sslmode=require"

# Crear todas las tablas
venv\Scripts\alembic.exe upgrade head

# (Opcional) Poblar con los datos masivos de prueba — tarda varios minutos
venv\Scripts\python.exe workers\seed_data.py

# Cierra esta terminal al terminar (para que DATABASE_URL vuelva a ser la local)
```

---

## 5. PARTE 4 — Subir las imágenes a Azure Container Registry

```powershell
# 1. Crear el registry (nombre único, SOLO minúsculas y números)
az acr create `
  --resource-group rg-auxilio `
  --name acrauxiliotunombre `
  --sku Basic `
  --admin-enabled true

# 2. Conectar tu Docker local con el registry
az acr login --name acrauxiliotunombre
```

### Construir y subir el BACKEND

```powershell
cd D:\SI2Parcial1\backend

# Construir la imagen con la "etiqueta" del registry
docker build -t acrauxiliotunombre.azurecr.io/auxilio-backend:v1 .

# Subirla (tarda según tu internet, la imagen pesa ~1 GB)
docker push acrauxiliotunombre.azurecr.io/auxilio-backend:v1
```

### Construir y subir el FRONTEND

> ⚠️ **ANTES de construir**, edita
> `frontend/src/environments/environment.development.ts` y cambia `apiUrl`
> por la URL que tendrá tu backend (la defines en la Parte 5):
>
> ```typescript
> apiUrl: 'https://api-auxilio-tunombre.azurewebsites.net'
> ```
> *(¿Por qué ese archivo y no environment.ts? Porque los servicios del
> proyecto importan `environment.development` directamente.)*

```powershell
cd D:\SI2Parcial1\frontend
docker build -t acrauxiliotunombre.azurecr.io/auxilio-frontend:v1 .
docker push acrauxiliotunombre.azurecr.io/auxilio-frontend:v1
```

---

## 6. PARTE 5 — Crear las Web Apps (donde corren los contenedores)

```powershell
# 1. UN solo plan B1 para las dos apps (~$13/mes en total)
az appservice plan create `
  --resource-group rg-auxilio `
  --name plan-auxilio `
  --is-linux `
  --sku B1

# 2. Web App del BACKEND (nombre único → será tu URL)
az webapp create `
  --resource-group rg-auxilio `
  --plan plan-auxilio `
  --name api-auxilio-tunombre `
  --container-image-name acrauxiliotunombre.azurecr.io/auxilio-backend:v1

# 3. Web App del FRONTEND
az webapp create `
  --resource-group rg-auxilio `
  --plan plan-auxilio `
  --name web-auxilio-tunombre `
  --container-image-name acrauxiliotunombre.azurecr.io/auxilio-frontend:v1

# 4. Darles permiso para descargar imágenes de tu registry
az webapp config container set --resource-group rg-auxilio --name api-auxilio-tunombre `
  --container-registry-url https://acrauxiliotunombre.azurecr.io
az webapp config container set --resource-group rg-auxilio --name web-auxilio-tunombre `
  --container-registry-url https://acrauxiliotunombre.azurecr.io
```

### Variables de entorno del backend (CRÍTICO)

Como el `.env` NO va dentro de la imagen, todas las variables se configuran
en App Service. **Copia los valores reales desde tu `backend/.env`:**

```powershell
az webapp config appsettings set `
  --resource-group rg-auxilio `
  --name api-auxilio-tunombre `
  --settings `
  WEBSITES_PORT=8000 `
  DATABASE_URL="postgresql://adminpg:TuPasswordSegura123!@pg-auxilio-tunombre.postgres.database.azure.com:5432/db?sslmode=require" `
  SECRET_KEY="<copia el de tu .env>" `
  CLOUDINARY_CLOUD_NAME="<de tu .env>" `
  CLOUDINARY_API_KEY="<de tu .env>" `
  CLOUDINARY_API_SECRET="<de tu .env>" `
  AZURE_SPEECH_KEY="<de tu .env>" `
  AZURE_SPEECH_REGION="southcentralus" `
  GROQ_API_KEY="<de tu .env>" `
  GEMINI_API_KEY="<de tu .env>" `
  VAPID_PUBLIC_KEY="<de tu .env>" `
  VAPID_PRIVATE_KEY="<de tu .env>" `
  STRIPE_SECRET_KEY="<de tu .env>" `
  STRIPE_WEBHOOK_SECRET="<de tu .env>" `
  STRIPE_PUBLISHABLE_KEY="<de tu .env>"
```

Explicaciones:
- `WEBSITES_PORT=8000` → le dice a App Service en qué puerto escucha tu
  contenedor. **Sin esto, la app nunca responde** (error típico nº 1).
- `SECRET_KEY` es **obligatoria** (sin ella el backend ni arranca).
- Si una variable tiene caracteres raros (`!`, `$`), ponla mejor desde el
  Portal: tu Web App → *Environment variables* → *Add*.

### Activar WebSockets (para el tracking en tiempo real)

```powershell
az webapp config set --resource-group rg-auxilio --name api-auxilio-tunombre --web-sockets-enabled true
```

### Arrancar y verificar

```powershell
az webapp restart --resource-group rg-auxilio --name api-auxilio-tunombre
az webapp restart --resource-group rg-auxilio --name web-auxilio-tunombre
```

Abre en el navegador (la primera carga tarda 1-2 min — está descargando la imagen):
- `https://api-auxilio-tunombre.azurewebsites.net/docs` → Swagger del backend ✔
- `https://web-auxilio-tunombre.azurewebsites.net` → tu app Angular ✔

---

## 7. PARTE 6 — Ajustes finales

### a) ¿El frontend no apunta al backend correcto?
Si te saltaste la edición del `apiUrl` antes de construir: edítalo ahora,
reconstruye y vuelve a subir (versiona la etiqueta):

```powershell
cd D:\SI2Parcial1\frontend
docker build -t acrauxiliotunombre.azurecr.io/auxilio-frontend:v2 .
docker push acrauxiliotunombre.azurecr.io/auxilio-frontend:v2

az webapp config container set --resource-group rg-auxilio --name web-auxilio-tunombre `
  --container-image-name acrauxiliotunombre.azurecr.io/auxilio-frontend:v2
az webapp restart --resource-group rg-auxilio --name web-auxilio-tunombre
```
*(Este mismo proceso —build con nueva etiqueta, push, config, restart— es
como se sube CUALQUIER cambio futuro, también del backend.)*

### b) App móvil Flutter
En `movil/lib/config/app_config.dart` cambia la URL base a
`https://api-auxilio-tunombre.azurewebsites.net` (y el WebSocket a
`wss://api-auxilio-tunombre.azurewebsites.net`). Nota el cambio
`http→https` y `ws→wss`.

### c) Stripe (webhook en producción)
En el [dashboard de Stripe](https://dashboard.stripe.com/test/webhooks):
*Add endpoint* → `https://api-auxilio-tunombre.azurewebsites.net/pagos/stripe/webhook`
→ evento `checkout.session.completed` → copia el nuevo `whsec_...` y
actualiza `STRIPE_WEBHOOK_SECRET` en las variables del App Service.
*(Recuerda: el flujo móvil funciona igual sin webhook gracias al endpoint
`/confirmar`, así que esto es opcional.)*

### d) Notificaciones Web Push
Ya funcionan mejor que en local: App Service da **HTTPS real**, que es lo
que el Service Worker de la PWA necesita. Solo recuerda que los usuarios
deben aceptar el permiso de notificaciones en el dominio nuevo.

### e) Módulo de IA local (CLIP / Ollama) — limitación honesta
El plan B1 tiene 1.75 GB de RAM: **no alcanza** para CLIP ni para Gemma.
- El resumen de incidentes funcionará en modo **plantilla** (el fallback
  que ya está implementado) y los reportes por lenguaje natural funcionan
  completos porque usan **Groq (nube)**.
- La clasificación de imágenes devolverá el 503 explicativo. Si la
  necesitas en la nube, requeriría un plan B3 (~$50/mes) — para la demo,
  muéstrala corriendo en tu laptop.

---

## 8. Verificación final (checklist)

- [ ] `https://api-...azurewebsites.net/docs` abre Swagger
- [ ] Login funciona desde el frontend desplegado
- [ ] El dashboard del admin carga KPIs (= la BD de Azure responde)
- [ ] Crear un incidente desde el móvil apuntando a la URL de Azure
- [ ] Tracking en tiempo real (= WebSockets habilitados)
- [ ] Reportes con IA (= GROQ_API_KEY bien configurada)

---

## 9. Solución de problemas

| Problema | Causa probable | Solución |
|----------|----------------|----------|
| La URL no responde / "Application Error" | Falta `WEBSITES_PORT=8000` o `SECRET_KEY` | Revisar variables y reiniciar |
| Quiero ver QUÉ está fallando | — | `az webapp log tail --resource-group rg-auxilio --name api-auxilio-tunombre` (logs en vivo del contenedor) |
| Error al crear un recurso: "subscription restricted / quota" | Región no permitida para estudiantes | Repetir con otra región de la lista (sección 3) |
| Backend no conecta a la BD | Falta `?sslmode=require` o firewall | Verificar la cadena; en el Portal: servidor PG → Networking → "Allow Azure services" ✔ |
| Frontend carga pero las peticiones fallan | `apiUrl` quedó en localhost dentro del build | Parte 6a (editar, rebuild, push) |
| Recargar una página del frontend da 404 | nginx sin fallback SPA | Ya resuelto en `nginx.conf` (try_files) — verifica que la imagen sea la actual |
| `docker push` da "unauthorized" | Sesión del registry expirada | `az acr login --name acrauxiliotunombre` de nuevo |
| Todo va lento la primera vez | B1 es modesto + arranque en frío | Normal; la segunda carga es rápida |

---

## 10. Cómo NO quemarte los $90

```powershell
# Ver cuánto llevas gastado:
#   Portal → Cost Management → Cost analysis

# APAGAR las apps cuando no las uses (dejan de consumir cómputo del plan,
# pero el plan B1 se cobra igual mientras exista):
az webapp stop --resource-group rg-auxilio --name api-auxilio-tunombre
az webapp stop --resource-group rg-auxilio --name web-auxilio-tunombre
az postgres flexible-server stop --resource-group rg-auxilio --name pg-auxilio-tunombre

# Volver a encender:
az webapp start ...   /   az postgres flexible-server start ...

# ☢️ BORRAR ABSOLUTAMENTE TODO (cuando termine el semestre):
az group delete --name rg-auxilio --yes
```

> La BD detenida no cobra cómputo pero sí almacenamiento (~$4/mes).
> El App Service Plan se cobra mientras exista: si vas a estar semanas sin
> usarlo, borra el plan y vuelve a crearlo cuando lo necesites (tus imágenes
> siguen en el registry, recrear todo toma 10 minutos con esta guía).

---

## Resumen de los comandos en orden (chuleta)

```powershell
az login
az group create --name rg-auxilio --location eastus2
az postgres flexible-server create ... (Parte 3)
az postgres flexible-server db create ...
alembic upgrade head (apuntando a Azure)
az acr create ... && az acr login ...
docker build + docker push (backend y frontend)
az appservice plan create --sku B1 --is-linux
az webapp create (x2)
az webapp config appsettings set ... (variables del backend)
az webapp config set --web-sockets-enabled true
az webapp restart (x2)
```
