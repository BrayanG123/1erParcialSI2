# Corrección de Coordenadas — Cochabamba/La Paz → Santa Cruz de la Sierra

**Fecha:** 2026-06-10
**Motivo:** El proyecto tenía coordenadas hardcodeadas de Cochabamba (seeders, mapas)
y de La Paz (centros por defecto de algunos mapas), pero el usuario está en
**Santa Cruz de la Sierra, Bolivia**.

---

## 1. Coordenadas utilizadas

| Ciudad | Latitud | Longitud | Dónde estaba |
|--------|---------|----------|--------------|
| Cochabamba (viejo) | -17.3895 | -66.1540 | seeders, tracking, dashboard, lecciones |
| La Paz (viejo) | -16.5000 | -68.1500 | mapa de registro de taller (web), selector de mapa (móvil) |
| **Santa Cruz (nuevo)** | **-17.7833** | **-63.1812** | todo |

> Ojo con el orden según la librería de mapas:
> - **Leaflet** (`L.map`): `center: [lat, lng]` → `[-17.7833, -63.1812]`
> - **MapLibre GL** (`maplibregl.Map`): `center: [lng, lat]` → `[-63.1812, -17.7833]`
> - **flutter_map** (`LatLng`): `LatLng(lat, lng)` → `LatLng(-17.7833, -63.1812)`

## 2. Archivos corregidos — Backend

| Archivo | Qué se cambió |
|---------|---------------|
| `backend/workers/seed_data.py` | `LAT_CENTRO` / `LNG_CENTRO`: ahora todos los talleres, mecánicos e incidentes del seed se generan alrededor de Santa Cruz (con radio aleatorio de ~0.05–0.18 grados) |
| `backend/app/routers/websocket.py` | Ejemplo de mensaje de ubicación en la documentación del endpoint WebSocket |

## 3. Archivos corregidos — Frontend Angular

| Archivo | Qué se cambió |
|---------|---------------|
| `frontend/.../setup-taller/setup-taller.component.ts` | El mapa de registro de taller abría en **La Paz**. Ahora abre en Santa Cruz (MapLibre, formato `[lng, lat]`). Si el navegador da permiso de GPS, igual hace `flyTo` a la ubicación real del usuario |
| `frontend/.../seguimiento/seguimiento.component.ts` | Constantes renombradas `COCHABAMBA_LAT/LNG` → `SANTA_CRUZ_LAT/LNG` con los valores nuevos (Leaflet, formato `[lat, lng]`) |
| `frontend/.../admin/admin-dashboard.component.ts` | Centro por defecto del mapa de densidad de incidentes. Solo aplica cuando no hay zonas con datos; si hay datos usa el promedio de las zonas reales |

## 4. Archivos corregidos — App móvil Flutter

| Archivo | Qué se cambió |
|---------|---------------|
| `movil/lib/features/cliente/screens/tracking_incidente_screen.dart` | `_latInicial` / `_lngInicial`: posición inicial del mapa de tracking cuando aún no hay posición del mecánico |
| `movil/lib/features/cliente/widgets/mapa_selector.dart` | `_defaultCenter` abría en **La Paz**. Ahora `LatLng(-17.7833, -63.1812)` |

## 5. Lecciones (.md) corregidas

| Lección | Qué tenía |
|---------|-----------|
| `modulo-2-flujo-incidente/leccion-2-2-flujo-completo.md` | Ejemplos JSON de `POST /incidentes` con lat/lng de Cochabamba (request y response) |
| `modulo-3-seeding/leccion-3-1-seed-masivo.md` | El bloque de código del seeder (espejo del archivo real) |
| `modulo-4-kpis/leccion-4-2-dashboard-angular.md` | Centro por defecto del mapa del dashboard + texto "Mapa de Cochabamba" |
| `modulo-5-websockets/leccion-5-2-tracking-ubicacion-mecanico.md` | Script JS de prueba que simula al mecánico enviando GPS |
| `modulo-5-websockets/leccion-5-3-integracion-angular.md` | Constantes del componente de seguimiento + script de prueba + texto descriptivo |

## 6. Verificación realizada

Se hizo un barrido (grep) de todo el proyecto buscando:
`-17.3895`, `-66.1540`, `-66.15`, `-16.5000`, `-68.1500`, `Cochabamba`, `COCHABAMBA`
→ **0 resultados restantes** (excluyendo `node_modules`).

## 7. ⚠️ Datos existentes en la BD

El cambio solo afecta a lo que se **genere de ahora en adelante**. Los registros que ya
están en tu base de datos (talleres, incidentes del seed anterior) siguen teniendo
coordenadas de Cochabamba — en el mapa aparecerán allá.

Para corregirlo: ejecuta la limpieza + re-seed descrita en `CAMBIOS-SEEDERS.md`
(sección 6). Un solo re-seed resuelve ambas cosas: la relación tenant 1:1 **y** las
coordenadas en Santa Cruz.

---

## Anexo — Otros cambios de esta sesión (referencia rápida)

No relacionados con coordenadas, pero hechos en la misma sesión por si revisas el diff:

1. **Vista "Asignaciones de Servicio"** (`asignaciones.component.ts/html`):
   ahora permite asignar mecánico desde la tarjeta, muestra la descripción del
   incidente, y ordena por fecha (toggle recientes/antiguas).
2. **Backend**: nuevo endpoint `PATCH /asignaciones/{id}/asignar-mecanico` que valida
   el mecánico del taller, cambia el estado a `taller_asignado` y **notifica al cliente
   por push** ("Se te asignó el mecánico X"). Registra en bitácora.
3. **Schema** `AsignacionRead` ahora incluye objetos anidados `incidente` (descripción)
   y `mecanico` (nombre del usuario) para que el front no muestre solo IDs.
