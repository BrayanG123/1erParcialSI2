FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar librerías de PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Exponer el puerto por defecto (Cloud Run usa la variable de entorno $PORT, pero exponemos 8000)
EXPOSE 8000

# Iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
