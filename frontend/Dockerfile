# ════════════════════════════════════════════════════════════
# Dockerfile del FRONTEND (Angular → nginx)
#
# Es un build "multi-etapa":
#   ETAPA 1 (build): usa Node para compilar Angular → archivos estáticos
#   ETAPA 2 (final): usa nginx (servidor web ultraliviano, ~25 MB)
#                    para servir esos archivos. Node NO va en la
#                    imagen final — por eso pesa poco.
#
# ⚠️ ANTES de construir: edita src/environments/environment.development.ts
#    y pon la URL real de tu backend en Azure (ver DESPLIEGUE-AZURE.md).
#
# Construir:  docker build -t auxilio-frontend .
# Probar:     docker run -p 8080:80 auxilio-frontend  →  http://localhost:8080
# ════════════════════════════════════════════════════════════

# ── ETAPA 1: compilar Angular ────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Copiar solo los manifests primero (caché de dependencias)
COPY package.json package-lock.json ./
RUN npm ci

# Copiar el resto del código y compilar para producción
COPY . .
RUN npm run build -- --configuration production

# ── ETAPA 2: servir con nginx ────────────────────────────────
FROM nginx:alpine

# Configuración de nginx con soporte para rutas de Angular (SPA)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar SOLO el resultado compilado de la etapa anterior
# (Angular 17+ genera la app dentro de dist/frontend/browser)
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80

# nginx arranca solo (CMD heredado de la imagen base)
