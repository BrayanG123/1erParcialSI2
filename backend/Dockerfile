# ════════════════════════════════════════════════════════════
# Dockerfile del BACKEND (FastAPI + Python 3.12)
#
# Construye una imagen liviana con todo lo necesario para correr
# la API. NO incluye el venv local ni el .env (ver .dockerignore):
# las variables de entorno se inyectan al ejecutar el contenedor.
#
# Construir:  docker build -t auxilio-backend .
# Probar:     docker run -p 8000:8000 --env-file .env auxilio-backend
# ════════════════════════════════════════════════════════════

# Imagen base: Python 3.12 "slim" (Debian mínimo, ~150 MB)
FROM python:3.12-slim

# Carpeta de trabajo dentro del contenedor
WORKDIR /code

# Buenas prácticas Python en contenedores:
#  - no generar .pyc  - logs sin buffer (se ven en tiempo real)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1. Copiar SOLO requirements primero (aprovecha la caché de Docker:
#    si no cambian las dependencias, este paso no se repite)
COPY requirements.txt .

# 2. Instalar dependencias (sin caché de pip para que la imagen pese menos)
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiar el código de la aplicación
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

# 4. Credenciales de Firebase para las notificaciones push.
#    El truco del corchete [n] hace la copia OPCIONAL: si el archivo
#    no existe, el build no falla (las push quedarían desactivadas).
COPY firebase_credentials.jso[n] ./

# Puerto en el que escucha la API
EXPOSE 8000

# Comando de arranque: uvicorn escuchando en TODAS las interfaces
# (0.0.0.0 es obligatorio dentro de un contenedor; "localhost" no funcionaría)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
