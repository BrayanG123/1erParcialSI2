# Docker en este Proyecto — Explicado para Aprender (y Depurar)

**Objetivo de este documento:** que entiendas QUÉ se hizo, POR QUÉ cada línea
está ahí, y CÓMO diagnosticar cuando algo falle. Es el complemento de
`DESPLIEGUE-AZURE.md` (aquél dice *qué comandos correr*; éste explica *cómo
funciona por dentro*).

---

## 1. Los conceptos, sin humo

### Imagen vs Contenedor (la diferencia que confunde a todos)

- **Imagen** = una plantilla congelada e inmutable. Como un "instalador" que
  ya trae el sistema operativo mínimo + Python + tus librerías + tu código.
  Se construye con `docker build` leyendo un `Dockerfile`.
- **Contenedor** = una imagen ejecutándose. Puedes lanzar 5 contenedores de
  la misma imagen. Cuando un contenedor muere, **todo lo que escribió dentro
  se pierde** (por eso la BD de producción no va en contenedor).

```
Dockerfile  ──docker build──►  Imagen  ──docker run──►  Contenedor
(receta)                       (plantilla)              (proceso vivo)
```

### Capas y caché (la clave para entender por qué el orden importa)

Cada instrucción del Dockerfile (`COPY`, `RUN`...) crea una **capa**. Docker
cachea las capas: si una instrucción y sus archivos no cambiaron, la reutiliza
sin ejecutarla de nuevo. **Por eso en nuestros Dockerfiles copiamos primero
`requirements.txt`/`package.json` y DESPUÉS el código:**

```
COPY requirements.txt .        ← cambia casi nunca → capa cacheada
RUN pip install ...            ← solo se re-ejecuta si requirements cambió
COPY app ./app                 ← cambia siempre → pero las capas de arriba ya están
```

Si copiáramos todo el código primero, **cada cambio de una línea de Python
re-instalaría TODAS las dependencias** (minutos perdidos en cada build).

---

## 2. El Dockerfile del backend, línea por línea

Archivo: `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim
```
La **imagen base**: un Debian mínimo con Python 3.12 ya instalado (~150 MB).
Elegí `slim` y no la normal (~1 GB) ni `alpine` (que da problemas al compilar
librerías como `psycopg2`). La versión 3.12 coincide con tu venv local —
**siempre alinea la versión del contenedor con la de desarrollo**.

```dockerfile
WORKDIR /code
```
Crea la carpeta `/code` dentro del contenedor y se "para" ahí. Todos los
`COPY` y comandos siguientes son relativos a esa ruta.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
```
Dos variables clásicas de Python en contenedores:
- la primera evita archivos `.pyc` (basura en la imagen),
- la segunda hace que los `print`/logs salgan **inmediatamente** — sin ella,
  `docker logs` se queda "mudo" hasta que el buffer se llena y crees que la
  app está colgada cuando no lo está. (Importante para depurar).

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
El patrón de caché explicado arriba. `--no-cache-dir` evita que pip guarde
los instaladores descargados dentro de la imagen (ahorra ~200 MB).

```dockerfile
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
```
Solo lo que producción necesita: el código (`app/`), las migraciones (por si
quieres correr `alembic` desde dentro del contenedor) y su config. Fíjate que
NO copiamos `venv/`, `workers/`, `media/` — eso lo bloquea el `.dockerignore`.

```dockerfile
COPY firebase_credentials.jso[n] ./
```
Truco interesante: el `[n]` convierte el nombre en un **patrón glob**, y los
COPY con patrón que no encuentran nada **no fallan**. Resultado: si el archivo
de credenciales de Firebase existe, entra; si no existe, el build sigue (y las
push notifications quedan desactivadas en vez de romper el build).

```dockerfile
EXPOSE 8000
```
Documentación: declara que la app escucha en el 8000. **No abre nada por sí
solo** — el mapeo real lo haces con `-p 8000:8000` al ejecutar.

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
El comando que corre al arrancar el contenedor. El detalle **crítico** es
`--host 0.0.0.0`: dentro de un contenedor, `localhost` significa "solo
accesible desde dentro del propio contenedor". Con `0.0.0.0` escucha en todas
las interfaces y el mapeo de puertos funciona. **Si algún día ves que el
contenedor corre pero nadie puede conectarse, sospecha de esto primero.**

### El `.dockerignore` del backend — por qué importa tanto

```
venv/          ← 1+ GB que NO sirve dentro de la imagen (las deps se instalan allá)
.env           ← ¡SECRETOS! Si entran en la imagen, cualquiera con la imagen los lee
__pycache__/   ← basura
workers/, media/, curso_fastapi/ ...  ← no son código de producción
```

Dos razones: **tamaño** (el "build context" que Docker procesa sería enorme) y
**seguridad** (una imagen se puede "desarmar" capa por capa con
`docker history` — un `.env` adentro es una fuga de claves).

---

## 3. El Dockerfile del frontend — build multi-etapa

Archivo: `frontend/Dockerfile`. Este es el concepto más elegante de los dos.

**El problema:** para compilar Angular necesitas Node + node_modules (~500 MB+).
Pero para *servir* el resultado solo necesitas un servidor de archivos
estáticos. Meter Node en la imagen final sería desperdiciar cientos de MB.

**La solución — dos etapas:**

```dockerfile
# ETAPA 1: la "fábrica" (se descarta al final)
FROM node:20-alpine AS build        # ← nota el alias "build"
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci                          # instala deps EXACTAS del lockfile
COPY . .
RUN npm run build -- --configuration production
```

`npm ci` (no `npm install`): instala exactamente lo que dice el
`package-lock.json`. Reproducible — el build de hoy y el de mañana usan las
mismas versiones.

```dockerfile
# ETAPA 2: la imagen final (solo nginx + archivos compilados)
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
```

`COPY --from=build` es la magia: copia archivos **desde la etapa anterior**.
Todo lo demás de la etapa 1 (Node, node_modules, código fuente) se descarta.
Resultado: imagen final de ~30 MB en vez de ~700 MB.

> Detalle específico de tu proyecto: Angular 17+ compila a
> `dist/frontend/browser` (con la subcarpeta `browser`). Si alguna vez el
> frontend desplegado muestra la página de bienvenida de nginx en vez de tu
> app, es porque esa ruta cambió y el COPY copió una carpeta vacía.

### El `nginx.conf` — los 3 bloques que importan

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```
**El más importante.** Angular es una SPA: rutas como `/admin/dashboard` no
existen como archivos — existen solo en el router de JavaScript. Sin esta
línea, entrar directo a una URL o presionar F5 daría **404**. Con ella, nginx
dice "¿no encuentro el archivo? → devuelvo index.html y que Angular resuelva".

```nginx
location = /ngsw-worker.js {
    add_header Cache-Control "no-cache";
}
```
El Service Worker de tu PWA **no debe cachearse**: es el archivo que detecta
si hay versión nueva de la app. Si el navegador lo cachea, tus usuarios
quedarían atrapados en versiones viejas.

```nginx
location ~* \.(js|css|png|...)$ {
    expires 30d;
}
```
Lo contrario para los assets: Angular les pone un hash en el nombre
(`main-X3F9A.js`), así que pueden cachearse agresivamente — si el contenido
cambia, el nombre cambia.

---

## 4. docker-compose.yml — orquestar los 3 servicios

Compose levanta varios contenedores como un solo sistema con `docker compose up`.
Lo que hay que entender de nuestro archivo:

### a) La red interna y los nombres mágicos

Compose crea una **red privada** donde cada servicio es alcanzable por su
nombre. Por eso el backend se conecta a la BD así:

```yaml
DATABASE_URL: postgresql://postgres:admin@db:5432/db
#                                       ^^ "db" = nombre del servicio, no una IP
```

Dentro de la red de compose, `db` resuelve al contenedor de PostgreSQL.
**Error clásico**: usar `localhost` en esa URL — dentro del contenedor del
backend, `localhost` es el propio backend, no la BD.

### b) Puertos: el formato `afuera:adentro`

```yaml
ports:
  - "5434:5432"   # tu máquina:contenedor
```
El PostgreSQL del contenedor escucha en su 5432, pero lo exponemos en el
**5434** de tu máquina porque tu PostgreSQL local ya ocupa el 5433. Si algo
dice "port is already allocated", es esto: cambia el número de la izquierda.

### c) El volumen: la memoria que sobrevive

```yaml
volumes:
  - pgdata:/var/lib/postgresql/data
```
Sin esto, cada `docker compose down` borraría todos los datos de la BD. El
volumen `pgdata` es una carpeta gestionada por Docker que persiste entre
reinicios. Solo se borra con `docker compose down -v` (la `-v` es deliberada).

### d) healthcheck + depends_on: el orden de arranque

```yaml
depends_on:
  db:
    condition: service_healthy
```
Sin esto, el backend arrancaría ANTES de que PostgreSQL esté listo y moriría
con "connection refused". El `healthcheck` ejecuta `pg_isready` cada 5 s y el
backend solo arranca cuando la BD responde. **Si el backend muere al arrancar
con errores de conexión, revisa que el healthcheck esté pasando**
(`docker compose ps` muestra el estado `healthy`).

### e) env_file + environment

```yaml
env_file: ./backend/.env          # carga TODAS tus claves actuales
environment:
  DATABASE_URL: ...@db:5432/db    # y SOBRESCRIBE solo esta
```
`environment` gana sobre `env_file`. Así reutilizamos tu `.env` real (Stripe,
Groq, etc.) pero apuntamos la BD al contenedor. El `.env` se inyecta **al
ejecutar** — nunca quedó dentro de la imagen.

---

## 5. Caja de herramientas para cuando algo falle

### Los 6 comandos que resuelven el 90% de los problemas

```powershell
# 1. ¿Qué está corriendo y en qué estado?
docker compose ps          # fíjate en STATUS: Up, Restarting, Exited, (healthy)

# 2. VER LOS LOGS (el comando más importante de todos)
docker compose logs backend          # logs del backend
docker compose logs -f backend      # -f = en vivo (como un tail)
docker compose logs --tail 50 db    # últimas 50 líneas de la BD

# 3. Entrar DENTRO de un contenedor vivo (para mirar con tus ojos)
docker compose exec backend sh
#   ya dentro puedes: ls, cat archivo, python -c "...", etc.  (salir: exit)

# 4. Reconstruir tras cambiar código (¡el build no se repite solo!)
docker compose up --build backend

# 5. Borrón y cuenta nueva (sin tocar los datos de la BD)
docker compose down && docker compose up --build

# 6. Ver imágenes y su peso / limpiar espacio en disco
docker images
docker system prune      # borra contenedores parados y capas huérfanas
```

### Tabla de diagnóstico: síntoma → causa → qué hacer

| Síntoma | Causa más probable | Cómo confirmarlo / arreglarlo |
|---------|--------------------|-------------------------------|
| El contenedor arranca y muere al instante (`Exited (1)`) | Error de Python al importar (falta una variable como SECRET_KEY) | `docker compose logs backend` — el traceback está ahí |
| `Exited (137)` | Se quedó sin RAM (137 = matado por el sistema) | Cierra programas; en tu laptop de 8 GB es el sospechoso nº 1 |
| Contenedor `Up` pero `localhost:8000` no responde | uvicorn escuchando en `localhost` en vez de `0.0.0.0`, o mapeo de puertos mal | Revisa el CMD del Dockerfile y el `ports:` del compose |
| Backend: "connection refused" a la BD | Usó `localhost` en vez de `db`, o la BD aún no estaba lista | Revisa DATABASE_URL; `docker compose ps` debe mostrar db `(healthy)` |
| "port is already allocated" | Otro programa usa ese puerto en tu máquina | Cambia el número IZQUIERDO del mapeo (`8001:8000`) |
| Cambié código pero no se refleja | Las imágenes no se reconstruyen solas | `docker compose up --build` |
| El build del frontend falla en `npm ci` | package-lock desincronizado | `npm install` local para regenerar el lock, commit, rebuild |
| Frontend muestra la página de nginx por defecto | El COPY de dist apuntó a una ruta vacía | Verifica que `dist/frontend/browser` exista tras un build local |
| F5 en una ruta de Angular da 404 | Falta el `try_files` de nginx | Ya está en nuestro nginx.conf — verifica que la imagen sea la actual |
| "no space left on device" | Capas viejas acumuladas | `docker system prune -a` (borra TODAS las imágenes no usadas) |
| Los logs no muestran nada y la app "parece" colgada | Buffer de Python | Ya resuelto con `PYTHONUNBUFFERED=1`; si lo quitas, vuelve |

### Cómo "leer" una imagen cuando dudas de qué tiene adentro

```powershell
# Historia de capas (qué instrucción creó cada una y cuánto pesa)
docker history auxilio-backend

# Inspección completa (variables, CMD, puertos declarados)
docker inspect auxilio-backend

# Correr un contenedor "de un solo uso" para explorar la imagen sin levantarla normal
docker run --rm -it auxilio-backend sh
```

---

## 6. El mapa mental completo

```
TU MÁQUINA (desarrollo)                     AZURE (producción)
─────────────────────────                   ─────────────────────────
docker compose up --build                   App Service ejecuta los
  ├── db        (postgres:16)  ◄── SOLO     contenedores que subiste
  ├── backend   (tu Dockerfile)    LOCAL    al Container Registry
  └── frontend  (tu Dockerfile)               ├── backend  ── conecta a ──► Azure PostgreSQL
                                            └── frontend                   (administrado, NO Docker)
       MISMAS IMÁGENES en ambos lados:
       lo que probaste local es EXACTAMENTE lo que corre en Azure.
       Esa es la promesa de Docker.
```

La única diferencia entre local y Azure son las **variables de entorno**
(DATABASE_URL apunta a `db:5432` local o a `...postgres.database.azure.com`
en la nube). El código y la imagen son idénticos — si funciona en tu compose,
funciona allá, y si falla allá, casi siempre es una variable mal puesta.
