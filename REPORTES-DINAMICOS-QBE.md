# Módulo: Reportes Dinámicos por Prompts — Fase 1 (Motor QBE)

**Fecha:** 2026-06-10
**Estado:** Fase 1 completa (backend + frontend). Fases 2 y 3 pendientes.

---

## 1. Visión general del proyecto

**Meta final:** el usuario escribe o dicta un texto → un LLM lo interpreta y lo
traduce a una estructura **QBE (Query by Example) en JSON** → el backend procesa
ese JSON de forma segura y genera el reporte (Gerencial o Ejecutivo).

**Hoja de ruta:**

| Fase | Contenido | Estado |
|------|-----------|--------|
| **1** | Estructura JSON del QBE + motor backend seguro + UI manual | ✅ Hecha |
| **2** | Prompt del LLM (Text-to-JSON) con Structured Outputs | Pendiente |
| **3** | Unir ambos: texto → LLM → QBE → motor → reporte | Pendiente |

**Decisión de arquitectura clave:** el LLM **nunca genera SQL**. Solo genera un
JSON con vocabulario cerrado (entidades, campos, operadores predefinidos). El
backend valida ese JSON contra whitelists y lo traduce él mismo a SQLAlchemy.
Así, aunque el LLM "alucine", lo peor que puede pasar es un HTTP 400 con un
mensaje que lista lo válido — nunca una fuga de datos ni inyección SQL.

---

## 2. Archivos creados

### Backend

| Archivo | Rol |
|---------|-----|
| `backend/app/schemas/reporte_qbe.py` | Contrato JSON (Pydantic): QBERequest, QBEResponse, enums de operadores y agregaciones |
| `backend/app/services/qbe_engine.py` | Motor: whitelists, traducción segura a SQLAlchemy, multi-tenant |
| `backend/app/routers/reporte_dinamico.py` | Endpoints `POST /reportes/qbe` y `GET /reportes/qbe/esquema` |
| `backend/app/main.py` | Registro del router (import + include_router) |

### Frontend

| Archivo | Rol |
|---------|-----|
| `frontend/src/app/core/services/reporte.service.ts` | Servicio HTTP + interfaces TS espejo del contrato |
| `frontend/src/app/features/admin/pages/reportes/reportes.component.ts` | Lógica del constructor de consultas |
| `frontend/src/app/features/admin/pages/reportes/reportes.component.html` | UI de dos paneles (constructor + resultados) |
| `frontend/src/app/app.routes.ts` | Ruta `/admin/reportes` (lazy) |
| `.../app-sidebar.component.ts` | Ítem "Reportes Dinámicos" en sección FINANZAS |

---

## 3. El contrato JSON del QBE

Este es el JSON que la Fase 2 le pedirá al LLM. Diseñado para ser **cerrado**
(todo enum/whitelist) y así apto para Structured Outputs.

```json
{
  "entidad": "pagos",
  "filtros": [
    {"campo": "estado", "operador": "igual", "valor": "pagado"},
    {"campo": "monto",  "operador": "mayor_que", "valor": 100}
  ],
  "rango_fechas": {"campo": "fecha_pago", "desde": "2026-01-01T00:00:00", "hasta": "2026-03-31T23:59:59"},
  "group_by": ["metodo"],
  "agregaciones": [
    {"funcion": "sumar",  "campo": "monto", "alias": "ingresos"},
    {"funcion": "contar", "alias": "cantidad"}
  ],
  "orden": {"campo": "ingresos", "direccion": "desc"},
  "pagina": 1,
  "tamano_pagina": 100
}
```

### Reglas del contrato

- **Sin `group_by` ni `agregaciones` → reporte GERENCIAL** (detalle): devuelve
  filas individuales con todos los campos de la whitelist.
- **Con `group_by` + `agregaciones` → reporte EJECUTIVO** (agrupado): devuelve
  una fila por grupo con los totales. Un agrupado sin agregaciones es error 400.
- `rango_fechas.campo` es opcional: si falta, el motor usa el campo de fecha
  por defecto de la entidad (ej: `fecha_pago` para pagos).
- `orden.campo` en modo agrupado puede ser el **alias de una agregación**
  (ej: ordenar por "ingresos").
- `agregacion.campo` es obligatorio salvo para `contar` (cuenta filas).
- `tamano_pagina` máximo: 1000.

### Operadores disponibles

`igual, distinto, mayor_que, mayor_igual, menor_que, menor_igual,
contiene, empieza_con, en_lista, es_nulo, no_es_nulo`

- `contiene` / `empieza_con` → ILIKE (case-insensitive)
- `en_lista` → el valor debe ser una lista no vacía
- `es_nulo` / `no_es_nulo` → no requieren valor

### Funciones de agregación

`contar, sumar, promedio, minimo, maximo`

### Respuesta (QBEResponse)

```json
{
  "entidad": "pagos",
  "tipo_reporte": "agrupado",
  "total": 2,
  "pagina": 1,
  "tamano_pagina": 100,
  "columnas": ["metodo", "ingresos", "cantidad"],
  "filas": [
    {"metodo": "efectivo", "ingresos": 354986.32, "cantidad": 877},
    {"metodo": "pasarela", "ingresos": 147835.22, "cantidad": 366}
  ]
}
```

`total` es el total SIN paginación (en agrupados, el número de grupos), lo que
permite al frontend calcular el número de páginas.

---

## 4. El motor (`qbe_engine.py`) — cómo funciona la seguridad

### Capa 1 — Whitelist de entidades

El dict `ENTIDADES` es la **única superficie** que el QBE puede tocar. Entidades
registradas: `incidentes, asignaciones, servicios, pagos, comisiones,
calificaciones, mecanicos, talleres`. Cualquier otra (ej: `usuarios`) → 400.

### Capa 2 — Whitelist de campos por entidad

Cada entidad mapea nombre expuesto → `Column` de SQLAlchemy de forma
**explícita**:

```python
"pagos": {
    "modelo": Pago,
    "campos": {
        "monto": Pago.monto,
        "estado": Pago.estado,
        ...
        "tipo_servicio": ServicioRealizado.tipo_servicio,  # campo traído por JOIN
    },
    "fecha_defecto": "fecha_pago",
    "tenant_col": ServicioRealizado.tenant_id,   # hereda tenant vía JOIN
    "joins": [ServicioRealizado],
},
```

**Nunca se usa `getattr(modelo, campo)` dinámico.** Si un campo no está en el
dict, no existe para el QBE — por eso `password_hash`, tokens, etc. son
inaccesibles aunque el LLM los pida.

### Capa 3 — Operadores cerrados y parametrizados

Los operadores son un Enum; `_condicion()` los traduce a expresiones SQLAlchemy
(`col == valor`, `col.ilike(...)`, `col.in_(...)`). Los valores siempre viajan
como **bind params** (`WHERE estado = %(estado_1)s`), nunca concatenados.

### Capa 4 — Aislamiento multi-tenant automático

Toda consulta se filtra por el `tenant_id` del administrador autenticado:

- Entidades con `tenant_id` propio (asignaciones, servicios, comisiones,
  mecánicos, talleres): filtro directo.
- Entidades SIN `tenant_id` (pagos, calificaciones): se hace JOIN con
  `servicios_realizados` y se filtra por `ServicioRealizado.tenant_id`.
- `incidentes` es global (`tenant_col: None`) porque pertenece al cliente,
  no al taller.

El admin **no puede pedir datos de otro taller** ni siquiera construyendo el
JSON a mano.

### Capa 5 — Tope de paginación

`tamano_pagina` validado por Pydantic con `le=1000`.

### Flujo interno de `ejecutar_qbe()`

```
1. Resolver entidad (whitelist) → cfg
2. ¿group_by/agregaciones? → construir SELECT agrupado o de detalle
3. Aplicar JOINs declarados + filtro de tenant
4. Aplicar filtros (cada campo validado contra whitelist)
5. Aplicar rango de fechas (campo explícito o el por defecto)
6. GROUP BY
7. total = q.count()   ← SQLAlchemy envuelve en subquery, correcto también para agrupados
8. ORDER BY (campo de whitelist o alias de agregación)
9. OFFSET/LIMIT → filas como dicts (r._mapping)
```

---

## 5. Endpoints

### `POST /reportes/qbe` (requiere admin)

Recibe el QBERequest, devuelve QBEResponse. Errores 400 descriptivos:

```
"Campo 'password_hash' no permitido para 'pagos'. Campos válidos: [...]"
"Entidad 'usuarios' no permitida. Entidades válidas: [...]"
```

> Estos mensajes son deliberadamente informativos: en la Fase 3 se pueden
> devolver al LLM para que se auto-corrija (retry loop).

### `GET /reportes/qbe/esquema` (requiere admin)

Devuelve el catálogo completo:

```json
{
  "entidades": {"pagos": {"campos": [...], "fecha_defecto": "fecha_pago"}, ...},
  "operadores": ["igual", "distinto", ...],
  "agregaciones": ["contar", "sumar", ...],
  "limites": {"tamano_pagina_max": 1000}
}
```

**Doble uso:** (a) el frontend construye sus selectores con esto; (b) en la
Fase 2 este mismo JSON se inyecta al prompt del sistema del LLM para que sepa
exactamente qué puede generar.

---

## 6. Frontend — `/admin/reportes`

Constructor visual de dos paneles (sidebar → FINANZAS → Reportes Dinámicos):

1. **Origen de datos**: entidad (cargada del esquema — si agregas una entidad
   al backend, aparece sola sin tocar el front) + toggle Gerencial/Ejecutivo.
2. **Filtros**: filas dinámicas campo/operador/valor. El input de valor se
   oculta con `es_nulo`/`no_es_nulo`; `en_lista` acepta "v1, v2, v3".
   Rango de fechas con date pickers (desde→00:00, hasta→23:59).
3. **Agrupación** (solo Ejecutivo): chips para `group_by` + agregaciones
   (función, campo, alias).
4. **Orden**: en Ejecutivo permite ordenar por los alias de las agregaciones.

Resultados: tabla de columnas dinámicas, paginación servidor, **exportar CSV**
(separador `;` y BOM UTF-8 para Excel), errores 400 mostrados tal cual.

**Detalle importante (casteo de tipos):** los inputs HTML entregan strings,
pero PostgreSQL rechaza comparar `Float` contra `"100"`. El componente castea
automáticamente antes de enviar: `"100"` → `100`, `"true"` → `true`,
resto → string. Ver `castear()` en `reportes.component.ts`.

---

## 7. Cómo extender el motor

### Agregar un campo a una entidad existente

En `qbe_engine.py`, añadir una línea al dict `campos`:

```python
"observaciones": ServicioRealizado.observaciones,
```

Nada más: el esquema, la validación y el frontend lo recogen automáticamente.

### Agregar una entidad nueva

Añadir una entrada a `ENTIDADES` con `modelo`, `campos`, `fecha_defecto`,
`tenant_col` y `joins`. Preguntas a responder:

1. ¿Tiene `tenant_id` propio? → `tenant_col` directo, `joins: []`.
2. ¿No lo tiene? → ¿a través de qué tabla se llega al tenant? → ese modelo va
   en `joins` y su `tenant_id` en `tenant_col` (ver `pagos` como ejemplo).
3. ¿Es global (sin tenant)? → `tenant_col: None` (ver `incidentes`).
4. **Nunca** incluir campos sensibles en la whitelist.

### Agregar un operador

1. Añadirlo al enum `OperadorFiltro` (schemas).
2. Añadir su rama en `_condicion()` (engine).
3. Si requiere valor, añadirlo a `_REQUIEREN_VALOR`.

---

## 8. Pruebas realizadas (contra la BD real con el seed)

| Prueba | Resultado |
|--------|-----------|
| Ejecutivo: pagos agrupados por método, suma+conteo, orden por alias | ✅ efectivo Bs 354.986 (877), pasarela Bs 147.835 (366) |
| Gerencial: asignaciones `estado=finalizado`, paginado a 2 | ✅ total 1243, 2 filas devueltas |
| Campo fuera de whitelist (`password_hash`) | ✅ HTTP 400 con lista de campos válidos |
| Entidad fuera de whitelist (`usuarios`) | ✅ HTTP 400 con lista de entidades válidas |
| SQL generado | ✅ 100% parametrizado (bind params en el log) |
| `ng build` frontend | ✅ compila sin errores |

Para repetir la prueba manual: Swagger en `/docs` → login admin →
`POST /reportes/qbe` con el JSON de ejemplo de la sección 3.

---

## 9. Plan para las fases siguientes

### Fase 2 — Text-to-JSON con LLM

- Endpoint nuevo `POST /reportes/desde-texto` que recibe `{"texto": "..."}`.
- Prompt del sistema construido con la salida de `describir_esquema()` +
  fecha actual (para que resuelva "el mes pasado", "este trimestre").
- **Structured Outputs**: forzar la respuesta del LLM al schema JSON de
  `QBERequest` (Pydantic ya lo genera con `QBERequest.model_json_schema()`).
- El JSON resultante entra por el MISMO `ejecutar_qbe()` — por eso el motor
  vive en `services/` y no en el router.

### Fase 3 — Integración y optimización

- En el frontend: campo de texto/dictado (ya existe el Speech-to-Text) arriba
  del constructor; la respuesta del LLM **pre-llena el formulario** para que
  el usuario revise/ajuste el QBE antes de ejecutar (humano en el loop).
- Retry loop: si el motor devuelve 400, reenviar el error al LLM para que
  corrija el QBE (los mensajes de error ya listan lo válido a propósito).
- Posible caché del esquema y de reportes frecuentes.
