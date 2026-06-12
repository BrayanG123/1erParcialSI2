# Auditoría del Proyecto contra la Ruta Crítica

**Fecha:** 2026-06-11
**Método:** revisión del código real del backend, web y móvil contra cada fase
de `RUTA_CRITICA.md`. **Solo diagnóstico — no se corrigió nada.**

---

## Resumen ejecutivo (semáforo por fase)

| Fase | Estado | Veredicto en una línea |
|------|--------|------------------------|
| 1. Cliente reporta incidente | 🟢 ~90% | Completa; falta el HistorialEstado inicial |
| 2. Búsqueda de talleres | 🟡 ~50% | Notifica a TODOS los admins (sin filtro); el motor inteligente existe pero es manual; sin temporizador ni penalización |
| 3. Taller acepta | 🟢 ~80% | Funciona end-to-end; falta SeguroVehicular y el historial del estado |
| 4. Cotización | 🔴 0% | No existe nada (ni modelo, ni endpoints, ni UI) |
| 5. Mecánico en camino (tracking) | 🟢 ~95% | La fase más completa del sistema |
| 6. Atención en sitio | 🟢 ~85% | Funciona, con un **bug serio** en el cierre (ver hallazgo #1) |
| 7. Servicio, pago, calificación | 🟢 ~85% | Pago (efectivo+Stripe), comisión 10% y calificación OK; bugs de tenant y notificación |
| Transversales (tenant, KPIs, PWA, reportes, offline) | 🟢 | En buen estado |

---

## 🔴 HALLAZGOS CRÍTICOS — bugs que probablemente no has visto

### #1 — Al completar el servicio, el cliente NO se entera (push ni WebSocket)

El flujo del mecánico en el móvil es: "Completar servicio" → formulario →
`POST /servicios-realizados`. Ese endpoint (`routers/servicio_realizado.py:64`)
finaliza la asignación llamando **directamente al CRUD**
`actualizar_estado_asignacion(...)` — pero las notificaciones push y el
broadcast por WebSocket del estado `finalizado` viven en el **router**
`PATCH /asignaciones/{id}/estado`, que en este camino nunca se ejecuta.

**Consecuencia real:** cuando el mecánico completa el trabajo por el camino
normal de la app, el cliente **no recibe** el push "Servicio finalizado,
califica y paga" (paso 3 de la Fase 7) y su pantalla de tracking **no se
entera del cierre** (sigue mostrando "en atención"). Solo se enteraría
recargando el detalle a mano.

### #2 — Los ServicioRealizado creados en producción quedan SIN tenant

`crud/servicio_realizado.py` no asigna `tenant_id` al crear (los del seed sí
lo tienen porque el seeder lo pone). Consecuencias en cadena para cada
servicio nuevo real:
- No aparece en reportes QBE de la entidad `servicios` (filtran por tenant).
- Los **pagos y calificaciones** de ese servicio tampoco aparecen en QBE
  (heredan el tenant vía JOIN con servicios).
- La **comisión** se crea sin tenant (el crud de comisión tampoco lo asigna).

La ruta crítica es explícita: *"tenant_id heredado del taller"* (Fase 7.1).

### #3 — HistorialEstado solo se escribe en 1 de los 5 cambios de estado

`HistorialEstado(...)` se instancia en **un único lugar**:
`actualizar_estado_asignacion` (los avances del mecánico). NO se registra:
- al crear el incidente (estado `pendiente` — Fase 1 lo exige),
- al crear la asignación (aceptación del taller),
- al pasar a `taller_asignado` (aceptar / asignar mecánico),
- al rechazar o cancelar.

La ruta crítica lo define como *"la fuente de verdad para los KPIs de
tiempo"*. Hoy los KPIs se calculan con `fecha_creacion`/`fecha_respuesta` de
la asignación (mitigación válida), pero el historial como auditoría completa
del ciclo **no existe** — en una defensa, si abren la tabla
`historial_estados`, solo verán los saltos del mecánico.

### #4 — "Rechazar" en Solicitudes disponibles no persiste nada

El botón Rechazar solo filtra el incidente de la lista **en memoria del
navegador** (con `confirm()`); al recargar la página reaparece. No existe el
concepto de "este taller rechazó → considerar al siguiente" (Fase 3.3).
Relacionado: tampoco existe el re-disparo de la Fase 2 si nadie acepta.

### #5 — Bug menor ya conocido: "Servicios activos" siempre 0

En Gestión de Mecánicos, el contador filtra por estados `'en_proceso'` y
`'asignado'`, que **no existen** (los reales: `taller_asignado`, `en_camino`,
`en_atencion`). Ya lo habíamos detectado; sigue pendiente.

### #6 — PATCH /asignaciones/{id}/estado no registra Bitácora

Los cambios de estado del mecánico (la columna vertebral del flujo) notifican
y emiten WS, pero **no escriben en Bitácora** — la ruta crítica pide bitácora
en Fases 5 y 6. Crear/aceptar/rechazar sí la registran.

---

## Detalle por fase

### FASE 1 — Cliente reporta incidente — 🟢

| Requisito | Estado |
|-----------|--------|
| Crear Incidente global (sin tenant) con GPS | ✅ |
| Evidencias (foto/audio vía Cloudinary) | ✅ |
| IA: transcripción de audio (Azure STT) | ✅ |
| IA: diagnóstico + categoría por texto (Groq) | ✅ endpoints `/incidentes/{id}/procesar-*` |
| IA: clasificación por imagen (CLIP) | ✅ implementado (requiere instalar deps) |
| Prioridad por tipo | ✅ (en Categoria.prioridad) |
| HistorialEstado inicial `pendiente` | ❌ (hallazgo #3) |
| Bitácora | ✅ |

Nota de diseño (aceptable, pero distinto al documento): el **Incidente** solo
tiene estados `disponible/no_disponible`; la cadena
`pendiente→…→finalizado` vive en **AsignacionServicio**. Conviene poder
explicar esa decisión en la defensa.

### FASE 2 — Búsqueda de talleres — 🟡 (la fase más débil)

| Requisito | Estado |
|-----------|--------|
| Filtrar por especialidad/distancia/disponibilidad | ⚠️ El algoritmo EXISTE (`/ia/asignacion-inteligente`, 5 criterios + radio por prioridad + ampliación automática) pero es **bajo demanda del admin**, no automático al crear el incidente |
| "Nunca notificar a todos" | ❌ `notificar_admins_nuevo_incidente` notifica a **TODOS** los admins del sistema (el propio código lo admite: "versión simple para el examen") |
| Registrar push en `notificaciones` | ✅ |
| Estado `buscando_taller` | ❌ existe en el enum pero nunca se usa |
| Temporizador de respuesta + penalización | ❌ no existe (`tiempo_limite_respuesta` no está en el modelo; no hay puntuación de prioridad del taller) |

**La conexión que falta** (y sería de alto valor): que al crear el incidente
se invoque el asignador inteligente y se notifique **solo a los talleres
candidatos**. Las dos piezas ya existen por separado.

### FASE 3 — Taller acepta — 🟢

| Requisito | Estado |
|-----------|--------|
| Ver incidente disponible con ficha IA, fotos, mapa | ✅ (resumen_ia, evidencias, ubicación) |
| SeguroVehicular del vehículo | ❌ **el modelo no existe en el proyecto** (Lección 9.3 del plan, nunca implementada) |
| Aceptar → AsignacionServicio con tenant_id | ✅ (corregido en esta serie de sesiones) |
| Notificar al cliente al aceptar | ✅ (corregido: antes no notificaba) |
| HistorialEstado `taller_asignado` | ❌ (hallazgo #3) |
| Rechazar → siguiente taller | ❌ (hallazgo #4) |
| Bitácora | ✅ |

### FASE 4 — Cotización — 🔴 NO EXISTE

No hay modelo `Cotizacion`, ni migración, ni endpoints, ni pantallas. Es
**el único gap de fase completa** contra la ruta crítica. (El doc la marca
"opcional" — decisión tuya si entra antes del examen.)

### FASE 5 — Tracking en tiempo real — 🟢 (la más sólida)

| Requisito | Estado |
|-----------|--------|
| Admin asigna mecánico desde la web | ✅ (+ push al cliente) |
| WS `ws/incidente/{id}` con broadcast de estados | ✅ |
| Mecánico envía GPS cada N seg | ✅ (pantalla de mapa del mecánico, cada 5 s) |
| Cliente ve al mecánico moverse en su mapa | ✅ |
| Última posición solo en memoria (no BD) | ✅ exactamente como recomienda el doc (manager + limpieza al finalizar) |
| Push "mecánico en camino" | ✅ |
| Offline del cliente | ✅ para crear incidentes (hive + UUID idempotente + sync); ⚠️ el "recordar último estado del tracking" es parcial |

### FASE 6 — Atención en sitio — 🟢 con el bug #1

| Requisito | Estado |
|-----------|--------|
| Transiciones validadas en_camino→en_atencion→finalizado | ✅ (con tabla de transiciones) |
| WS emite cambios | ✅ vía PATCH /estado… ❌ pero NO en el cierre real (hallazgo #1) |
| HistorialEstado con timestamp | ✅ (único lugar donde sí se escribe) |
| Bitácora | ❌ (hallazgo #6) |

### FASE 7 — Servicio, pago, calificación — 🟢

| Requisito | Estado |
|-----------|--------|
| ServicioRealizado al finalizar | ⚠️ No es automático: el mecánico lo registra con formulario y ESO dispara el `finalizado` (orden invertido pero funcionalmente válido) |
| Timestamps inicio/fin + duración | ❌ solo `fecha_realizado`; sin duración real almacenada |
| tenant_id heredado | ❌ (hallazgo #2) |
| Evaluación SLA | ✅ existe en `kpi.py` (KPI de cumplimiento) — calculado desde las fechas de la asignación |
| Push "califica y paga" | ❌ por el hallazgo #1 |
| Pago desde la app | ✅ efectivo (admin confirma) + **Stripe Checkout** completo |
| Comisión 10% | ✅ (`PORCENTAJE_COMISION = 10.0`, se crea al confirmar pago) |
| Estado de pago `fallido` + reintento | ⚠️ solo existe `pendiente/pagado`; el flujo Stripe permite reintentar de facto, pero no hay estado fallido |
| Calificación 1-5 + comentario | ✅ y además actualiza `calificacion_promedio` de taller Y mecánico (mejor que lo pedido) |

### Transversales — 🟢

- **Multi-tenant**: aislamiento en endpoints clave y QBE; relación tenant↔taller 1:1 corregida. ✅
- **KPIs/Dashboard**: implementados incluyendo SLA, ranking, zonas. ✅
- **Reportes dinámicos**: QBE + lenguaje natural (texto/voz) + PDF/Excel/correo. ✅ (supera lo pedido)
- **PWA + Web Push / FCM móvil**: funcionando (verificado por ti). ✅
- **Offline Flutter**: implementado. ✅
- **Docker + guía Azure**: listos. ✅

---

## Prioridades sugeridas (si decides corregir)

| # | Qué | Esfuerzo | Por qué primero |
|---|-----|----------|-----------------|
| 1 | Hallazgo #1: notificar + WS al completar servicio | Bajo (mover la lógica al endpoint de servicios o reutilizar la del router de estado) | Rompe la experiencia del cliente en el cierre, el momento más visible de una demo |
| 2 | Hallazgo #2: tenant_id en ServicioRealizado (y Comision) | Bajo | Corrompe silenciosamente los datos nuevos para reportes/KPIs |
| 3 | Hallazgo #3: escribir HistorialEstado en crear/aceptar/asignar | Bajo-medio | Auditoría completa del ciclo; defensa del examen |
| 4 | Fase 2 automática: asignador inteligente + notificar solo candidatos al crear incidente | Medio | Convierte la fase más débil en una fortaleza usando piezas ya hechas |
| 5 | Hallazgos #5 y #6 (contador de servicios activos; bitácora en cambios de estado) | Trivial | Pulido |
| 6 | Fase 4 Cotización / SeguroVehicular | Alto / Medio | Solo si el enunciado del examen los exige (el doc marca cotización como opcional) |

> Nota honesta: los puntos donde el sistema se aparta del documento pero
> funciona (estados del incidente simplificados, ServicioRealizado manual en
> vez de automático) **no son errores** — son decisiones defendibles. Lo
> importante es poder explicarlas; este documento te da el argumento.
