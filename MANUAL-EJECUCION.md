# Manual de Ejecución del Proyecto — Desde Cero

**Para quién:** alguien que acaba de clonar el repositorio y quiere correr el
sistema completo en su PC (Windows). Sigue las secciones en orden.

**El sistema tiene 3 partes** que corren por separado:

| Parte | Tecnología | Puerto | Carpeta |
|-------|-----------|--------|---------|
| Backend (API) | FastAPI + Python 3.12 | 8000 | `backend/` |
| App web (admin/taller) | Angular | 4200 | `frontend/` |
| App móvil (cliente/mecánico) | Flutter | — | `movil/` |

Más la base de datos **PostgreSQL** (puerto 5433) y, opcionalmente, los
motores de IA.

---

## 0. Requisitos previos (instalar una sola vez)

| Programa | Versión | Para qué | Descarga |
|----------|---------|----------|----------|
| Python | 3.12.x | Backend | python.org (marcar "Add to PATH") |
| PostgreSQL | 16 | Base de datos | postgresql.org |
| Node.js | 20+ | Frontend Angular | nodejs.org |
| Flutter SDK | 3.5+ | App móvil | docs.flutter.dev |
| Git | — | Clonar el repo | git-scm.com |
| Docker Desktop | — | OPCIONAL (atajo, ver sección 7) | docker.com |

> **Configuración esperada de PostgreSQL:** el proyecto asume usuario
> `postgres`, contraseña `admin`, **puerto 5433** y una base llamada `db`.
> Si tu instalación usa otros valores, ajusta `DATABASE_URL` en el `.env`
> (sección 1.2) — no hace falta tocar nada más.

Crear la base de datos (una vez, en una terminal):
```powershell
# Te pedirá la contraseña del usuario postgres
psql -U postgres -p 5433 -c "CREATE DATABASE db;"
```

---

## 1. BACKEND (FastAPI)

### 1.1 Entorno virtual y dependencias

```powershell
cd backend

# Crear el entorno virtual (carpeta venv/)
python -m venv venv

# Instalar las dependencias (~5 min la primera vez)
venv\Scripts\pip.exe install -r requirements.txt
```

### 1.2 El archivo `.env` (configuración y claves)

El backend lee su configuración de `backend/.env`. **Este archivo NO viene
en el repositorio** (contiene claves privadas). Créalo con este contenido:

```env
# ── OBLIGATORIAS (sin esto el backend no arranca) ─────────────
DATABASE_URL=postgresql://postgres:admin@localhost:5433/db
SECRET_KEY=cualquier-cadena-larga-y-aleatoria-para-firmar-los-jwt

# ── OPCIONALES: cada una habilita una funcionalidad ───────────
# (el sistema arranca sin ellas; la funcionalidad queda desactivada)

# Subida de fotos/audios de incidentes (cloudinary.com, plan gratis)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Speech-to-Text: dictado de incidentes y de reportes (portal.azure.com)
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=southcentralus

# IA en la nube: diagnóstico de incidentes y reportes por lenguaje natural
GROQ_API_KEY=          # console.groq.com (gratis)
GEMINI_API_KEY=        # aistudio.google.com (gratis)

# Notificaciones push a la app móvil (consola de Firebase)
# Además requiere el archivo backend/firebase_credentials.json
# (Firebase Console → Configuración → Cuentas de servicio → Generar clave)

# Notificaciones push del navegador (web push / PWA)
# Generar el par de claves con:
#   venv\Scripts\python.exe -c "from py_vapid import Vapid01; v=Vapid01(); v.generate_keys(); print('PUB:', v.public_pem()); print('PRIV:', v.private_pem())"
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=

# Pagos con tarjeta (dashboard.stripe.com → modo test)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PUBLISHABLE_KEY=

# Envío de reportes por correo (Gmail + App Password, ver REPORTES-EXPORTAR-CORREO.md)
SMTP_USER=
SMTP_PASSWORD=

# IA local con Ollama (ver sección 5 y MODULO-IA.md)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODELO=gemma2:2b
```

### 1.3 Crear las tablas y poblar con datos de prueba

```powershell
# Crear todas las tablas (migraciones de Alembic)
venv\Scripts\alembic.exe upgrade head

# OPCIONAL pero recomendado: datos masivos de prueba
# (20 talleres con su tenant, 100 mecánicos, 500 clientes, 2000 incidentes)
# Tarda 1-5 minutos.
venv\Scripts\python.exe workers\seed_data.py
```

### 1.4 Arrancar el backend

```powershell
# --host 0.0.0.0 es IMPORTANTE: permite que la app móvil (otro
# dispositivo en tu red WiFi) pueda conectarse al backend
venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

Verificar: abre **http://localhost:8000/docs** → debe aparecer Swagger con
todos los endpoints. Deja esta terminal abierta (el backend corre ahí).

### Credenciales de prueba (si corriste el seed)

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Admin del taller 1 | `adm_t1_a0` | `Test1234` |
| Mecánico del taller 1 | `mec_t1_m0` | `Test1234` |
| Cliente | `cli_0000` | `Test1234` |

---

## 2. FRONTEND WEB (Angular) — modo desarrollo

Para trabajar en el código día a día:

```powershell
cd frontend

# Instalar dependencias (~5 min la primera vez)
npm install

# Levantar el servidor de desarrollo
npx ng serve
```

Abrir **http://localhost:4200** → login con las credenciales de prueba.

> El frontend apunta al backend según `apiUrl` en
> `src/environments/environment.development.ts` (por defecto
> `http://localhost:8000`). Si tu backend corre en otra máquina/puerto,
> cámbialo ahí.

⚠️ **Limitación del modo desarrollo:** el Service Worker de la PWA NO se
activa con `ng serve` — por lo tanto las **notificaciones push del
navegador no funcionan** en este modo. Para probarlas, usa la sección 3.

---

## 3. FRONTEND WEB — modo producción con http-server (PWA + notificaciones)

El Service Worker (y con él: la PWA instalable, el modo offline y las
notificaciones web push) **solo existe en el build de producción**. Para
probarlo:

```powershell
cd frontend

# 1. Compilar para producción (genera dist/frontend/browser)
npx ng build --configuration production

# 2. Servir el build con http-server
#    -p 4200 → mismo puerto de siempre
#    -c-1    → sin caché (clave para que el SW detecte versiones nuevas)
npx http-server dist\frontend\browser -p 4200 -c-1
```

Abrir **http://localhost:4200**. Ahora sí:
- El navegador ofrece "Instalar aplicación" (PWA)
- Al hacer login como admin aparece el banner para **activar notificaciones**
  (acéptalo; si no aparece el permiso, revisa
  `chrome://settings/content/notifications` y permite `localhost:4200`)
- Al crear un incidente desde el móvil, llega la notificación al navegador

> Cada vez que cambies código tienes que **volver a compilar** (paso 1) —
> http-server solo sirve archivos, no recompila.

---

## 4. APP MÓVIL (Flutter)

```powershell
cd movil

# Instalar dependencias
flutter pub get
```

### Configurar la IP del backend

La app móvil corre en un teléfono/emulador — "localhost" ahí NO es tu PC.
Edita `lib/config/app_config.dart` y pon la **IP de tu PC en la red WiFi**:

```powershell
# Para conocer tu IP (busca "IPv4" del adaptador WiFi):
ipconfig
```

```dart
// app_config.dart — ejemplo con IP 192.168.0.15
baseUrl = 'http://192.168.0.15:8000'
wsBaseUrl = 'ws://192.168.0.15:8000'
```

Requisitos: el teléfono y la PC en la **misma red WiFi**, y el backend
levantado con `--host 0.0.0.0` (sección 1.4). Si no conecta, prueba
desactivar temporalmente el Firewall de Windows o crear una regla para
el puerto 8000.

### Ejecutar

```powershell
# Con el teléfono conectado por USB (depuración USB activa) o un emulador:
flutter devices          # verificar que aparece
flutter run              # compila e instala (~5 min la primera vez)
```

---

## 5. MÓDULO DE IA (opcional — el sistema funciona sin esto)

Guía completa en **MODULO-IA.md**. Resumen de qué necesita cada función:

| Función | Qué necesita | Sin eso, ¿qué pasa? |
|---------|--------------|---------------------|
| Reportes por lenguaje natural (texto/voz) | `GROQ_API_KEY` en `.env` (nube, gratis) | El botón "Generar con IA" devuelve error claro |
| Dictado por voz | `AZURE_SPEECH_KEY` en `.env` | El micrófono devuelve error claro |
| Resumen/ficha del incidente | Nada (plantilla) u Ollama para LLM real | Funciona siempre (modo plantilla) |
| Asignación inteligente de talleres | Nada | Funciona siempre |
| Clasificación de fotos (CLIP) | `pip install torch...` (ver abajo) | Endpoint devuelve 503 con instrucciones |

### Ollama (LLM local para los resúmenes) — opcional

```powershell
# 1. Instalar Ollama: https://ollama.com/download/windows
# 2. Descargar el modelo (~1.6 GB, una sola vez):
ollama pull gemma2:2b
```
Listo: queda como servicio en `localhost:11434` y el backend lo detecta solo.

### CLIP (clasificación de imágenes) — opcional, ~1.3 GB

```powershell
cd backend
# ⚠️ el --index-url es importante (versión CPU, no la de 2.5 GB con CUDA)
venv\Scripts\pip.exe install torch --index-url https://download.pytorch.org/whl/cpu
venv\Scripts\pip.exe install -r requirements-ia.txt
```
La primera clasificación descarga el modelo (~600 MB) automáticamente.

Verificar el estado de todo: `GET /ia/estado` en Swagger.

---

## 6. ORDEN DE ARRANQUE DIARIO (resumen)

Cada parte en su propia terminal:

```powershell
# Terminal 1 — Backend
cd backend
venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Web (elegir UNO de los dos modos)
cd frontend
npx ng serve                                          # desarrollo
# — o —
npx http-server dist\frontend\browser -p 4200 -c-1    # producción/PWA

# Terminal 3 — Móvil (opcional)
cd movil
flutter run

# (Ollama arranca solo como servicio de Windows si lo instalaste)
```

PostgreSQL corre como servicio de Windows — no hay que arrancarlo a mano.

---

## 7. ALTERNATIVA RÁPIDA: todo con Docker

Si tienes Docker Desktop y solo quieres VER el sistema funcionando (sin
ambiente de desarrollo):

```powershell
# En la raíz del proyecto (necesitas igual el backend/.env de la sección 1.2)
docker compose up --build
```

- Backend → http://localhost:8000/docs
- Web (build de producción) → http://localhost:8080
- PostgreSQL propio del compose → puerto 5434 (BD vacía: correr migraciones
  y seed contra `localhost:5434` si quieres datos)

Detalles y depuración: **DOCKER-EXPLICADO.md**.

---

## 8. Problemas comunes

| Problema | Causa | Solución |
|----------|-------|----------|
| Backend: `ValidationError ... SECRET_KEY` | Falta el `.env` o la variable | Sección 1.2 |
| Backend: `connection refused` a la BD | PostgreSQL apagado o puerto distinto | Servicios de Windows → postgresql; revisar puerto en `DATABASE_URL` |
| `alembic upgrade head` falla | La BD `db` no existe | Crearla (sección 0) |
| Web: "Verifica que el servidor esté activo" | Backend apagado o `apiUrl` mal | Arrancar backend; revisar `environment.development.ts` |
| Móvil no conecta | IP mal, redes distintas, firewall, o falta `--host 0.0.0.0` | Sección 4 |
| No llegan notificaciones web | Estás en `ng serve` (sin Service Worker) | Usar la sección 3; permitir notificaciones en Chrome |
| No llegan push al móvil | Falta `firebase_credentials.json` o el cliente no tiene token | Probar `POST /notificaciones/test-push/incidente/{id}` — devuelve el diagnóstico exacto |
| `flutter run` falla | SDK desactualizado o licencias | `flutter doctor` y seguir lo que indique |
| Puerto 8000/4200 ocupado | Otro proceso lo usa | Cambiar `--port` / `-p`, o cerrar el proceso |

---

## 9. Mapa de documentación del proyecto

| Documento | Tema |
|-----------|------|
| `MANUAL-EJECUCION.md` | Este archivo — correr el proyecto |
| `MODULO-IA.md` | Módulo de IA: instalación y uso detallado |
| `REPORTES-DINAMICOS-QBE.md` | Motor de reportes QBE (arquitectura) |
| `REPORTES-EXPORTAR-CORREO.md` | Exportar PDF/Excel y envío por correo (config SMTP) |
| `DOCKER-EXPLICADO.md` | Cómo funciona la dockerización + depuración |
| `DESPLIEGUE-AZURE.md` | Subir todo a Azure paso a paso |
| `RUTA_CRITICA.md` | El flujo de negocio completo del sistema |
| `CAMBIOS-SEEDERS.md` / `CAMBIOS-COORDENADAS.md` | Historial de correcciones |
