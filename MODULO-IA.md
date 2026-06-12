# Módulo de Inteligencia Artificial — Guía Completa

**Fecha:** 2026-06-11
**Estado:** Implementado y verificado. Pendiente de tu parte: instalar las
dependencias de visión (cuando liberes recursos) y Ollama (opcional).

---

## 1. Qué se implementó y por qué así

El módulo tiene **tres motores independientes**, diseñados específicamente
para tu hardware (8 GB RAM con ~2 GB libres, i5 8th gen, GPU integrada):

| Motor                        | Tecnología                 | RAM que consume                 | ¿Funciona ya? |
|-------                       |-----------                 |-----------------                |----------------|
| 1. Clasificación de imágenes | CLIP ViT-B/32 (local, CPU) | ~600 MB **solo cuando se usa** | Requiere instalar dependencias (sección 3) |
| 2. Generación de resumen | Gemma 2B vía **Ollama** + fallback a plantilla | ~2 GB (proceso aparte de Ollama) | ✅ SÍ (en modo plantilla, sin instalar nada) |
| 3. Asignación inteligente | Algoritmo de puntuación multi-criterio (Python puro) | 0 MB extra | ✅ SÍ (probado con tu BD: funciona) |

### Decisiones clave de diseño (lee esto para entender el porqué)

**a) Carga perezosa (lazy loading).** Ningún modelo se carga al arrancar el
backend. CLIP se carga en RAM la *primera vez* que alguien clasifica una
imagen y queda en memoria para las siguientes. Si nunca usas ese endpoint,
no gasta ni 1 MB. Además, **el backend arranca aunque las librerías de IA
no estén instaladas** (los imports están dentro de las funciones, no al
inicio del archivo) — esto ya está verificado.

**b) CLIP en modo "zero-shot".** CLIP compara la imagen contra descripciones
de texto y elige la más parecida. No hubo que entrenar nada: definimos
descripciones en inglés por cada categoría (batería, llanta, choque, motor,
otros) y el modelo decide. Es el enfoque correcto para tu caso: modelo
pequeño (~600 MB), corre en CPU en 2-4 segundos por imagen.

**c) Gemma 2B corre en Ollama, NO dentro de Python.** Ollama es un programa
aparte que gestiona el modelo: lo carga al usarlo y lo descarga de memoria
tras unos minutos de inactividad. Si lo metiéramos dentro del proceso de
FastAPI, el backend pesaría +2 GB de RAM permanentes — inviable en tu equipo.

**d) Fallback a plantilla.** Si Ollama no está corriendo (o no lo instalas
nunca), el generador de resumen usa una plantilla estructurada con los datos
reales del incidente. El endpoint **jamás falla por falta de hardware**.
La respuesta siempre indica qué se usó: `"modelo_usado": "gemma2:2b (ollama)"`
o `"plantilla (sin LLM)"`.

**e) La asignación inteligente NO usa un modelo de IA** — y eso es correcto.
Es un problema de decisión multi-criterio: lo profesional es un algoritmo de
puntuación determinista y **explicable** (puedes defender cada número en el
examen), no una caja negra. Consume 0 MB extra.

---

## 2. Archivos creados/modificados

```
backend/
├── app/services/ia/                  ← NUEVO paquete de IA
│   ├── __init__.py                   ← descripción del paquete
│   ├── clasificador_imagen.py        ← Motor 1: CLIP (visión artificial)
│   ├── generador_resumen.py          ← Motor 2: Gemma 2B/Ollama + plantilla
│   └── asignador_inteligente.py      ← Motor 3: puntuación de talleres
├── app/routers/ia.py                 ← NUEVO: los 4 endpoints
├── app/main.py                       ← registro del router
├── app/config.py                     ← OLLAMA_URL y OLLAMA_MODELO
└── requirements-ia.txt               ← NUEVO: deps de visión (NO instaladas aún)
```

Todo el código tiene comentarios explicando qué hace cada parte.

---

## 3. INSTALACIÓN — paso a paso (hazlo cuando liberes tu equipo)

### Parte A — Visión artificial (CLIP) — ~1.3 GB de disco

> Necesario SOLO para `POST /ia/clasificar-imagen`. El resto del módulo
> funciona sin esto.

```powershell
# 1. Abrir PowerShell en D:\SI2Parcial1\backend

# 2. Instalar PyTorch versión CPU
#    ⚠️ MUY IMPORTANTE el --index-url: sin él, pip instala la versión con
#    CUDA que pesa 2.5+ GB y no te sirve (tu GPU es integrada)
venv\Scripts\pip.exe install torch --index-url https://download.pytorch.org/whl/cpu

# 3. Instalar transformers y pillow
venv\Scripts\pip.exe install -r requirements-ia.txt
```

La **primera vez** que uses el endpoint de clasificación, se descargará el
modelo CLIP (~600 MB) automáticamente a `C:\Users\USUARIO\.cache\huggingface\`.
Esa primera llamada tardará varios minutos (descarga + carga). Las siguientes
tardan 2-4 segundos.

> 💡 **Consejo de RAM:** antes de clasificar imágenes por primera vez,
> cierra pestañas de Chrome. CLIP necesita ~600 MB libres al cargarse.

### Parte B — Gemma 2B con Ollama (opcional) — ~2 GB de disco

> Necesario SOLO si quieres que el resumen lo redacte un LLM de verdad.
> Sin esto, el resumen sale por plantilla (que ya funciona).

```powershell
# 1. Descargar e instalar Ollama para Windows:
#    https://ollama.com/download/windows
#    (instalador normal, siguiente-siguiente)

# 2. Descargar el modelo Gemma 2B (una sola vez, ~1.6 GB):
ollama pull gemma2:2b

# 3. Verificar que funciona:
ollama run gemma2:2b "Hola, preséntate en una frase"
#    (escribe /bye para salir del chat)
```

Ollama queda corriendo como servicio en `http://localhost:11434`. El backend
lo detecta solo — no hay que configurar nada más. Si algún día quieres usar
otro modelo, cambia `OLLAMA_MODELO` en el `.env` (ej: `OLLAMA_MODELO=phi3:mini`).

> ⚠️ **Sobre tu RAM:** Gemma 2B necesita ~2 GB libres mientras genera.
> Con 6 GB ya ocupados va a estar MUY justo. Recomendaciones:
> - Cierra Chrome (o deja 2-3 pestañas) antes de generar resúmenes.
> - Ollama descarga el modelo de memoria tras ~5 min sin uso — no queda
>   ocupando RAM permanentemente.
> - Si va demasiado lento o se congela, simplemente cierra Ollama:
>   el sistema cae a plantilla automáticamente.

---

## 4. CÓMO USAR — los 4 endpoints (vía Swagger)

Levanta el backend normal (`uvicorn app.main:app --reload`), entra a
`http://localhost:8000/docs` y haz login como **administrador** (Authorize).

### 4.1 `GET /ia/estado` — verifica qué está listo

Empieza SIEMPRE por aquí. Devuelve algo como:

```json
{
  "vision_artificial": {
    "dependencias_instaladas": false,    ← false hasta que hagas la Parte A
    "modelo_en_memoria": false,
    "modelo": "openai/clip-vit-base-patch32"
  },
  "generador_resumen": {
    "ollama_corriendo": false,           ← false hasta que instales Ollama
    "modelo_descargado": false,
    "modelo": "gemma2:2b"
  },
  "asignador_inteligente": { "disponible": true }
}
```

### 4.2 `POST /ia/clasificar-imagen` — visión artificial

Dos formas de usarlo:

**a) Subiendo una foto directamente:** en Swagger, expande el endpoint,
"Try it out", selecciona un archivo en el campo `archivo` y ejecuta.

**b) Con la foto de un incidente existente:** deja `archivo` vacío y pon
`incidente_id = 5` en los parámetros. Usa la foto del incidente
(o su primera evidencia tipo foto).

**Extra:** si además pones `actualizar_categoria = true`, el sistema
actualiza la categoría del incidente en la BD según lo que vio la IA.

Respuesta:
```json
{
  "categoria": "llanta",
  "confianza": 0.8731,
  "prioridad_sugerida": 1,
  "puntuaciones": { "llanta": 0.8731, "choque": 0.0612, "otros": 0.034, ... },
  "modelo": "openai/clip-vit-base-patch32"
}
```

> La primera llamada tras reiniciar el backend tarda más (carga del modelo).
> Si no instalaste las dependencias, devuelve **503** con las instrucciones
> exactas de qué instalar — no un error críptico.

### 4.3 `POST /ia/resumen/{incidente_id}` — ficha estructurada

Ejecútalo con el id de cualquier incidente. Hace tres cosas:
1. Genera la ficha (Gemma 2B si Ollama corre; plantilla si no)
2. La guarda en `incidente.resumen_ia` (visible para las apps)
3. Registra la ejecución en la tabla `procesamientos_ia` (auditoría:
   estado, modelo usado, fechas, error si hubo)

```json
{
  "incidente_id": 12,
  "ficha": "RESUMEN: ...\nTIPO DE PROBLEMA: ...\nNIVEL DE URGENCIA: ...\nRECOMENDACIÓN AL TALLER: ...",
  "modelo_usado": "plantilla (sin LLM)",
  "procesamiento_id": 3
}
```

> Con Ollama corriendo, la generación tarda 15-60 segundos en tu CPU.
> Con plantilla es instantánea.

### 4.4 `GET /ia/asignacion-inteligente/{incidente_id}` — mejor taller

**Ya funciona — fue probado con tu BD real** (evaluó 22 talleres y
seleccionó el mejor con desglose). Devuelve:

```json
{
  "incidente_id": 2008,
  "criterios": {
    "categoria": "Llanta pinchada",
    "prioridad": 1,
    "radio_busqueda_km": 15.0,
    "radio_ampliado": false,
    "especialidades_buscadas": ["llantas y suspensión", "auxilio en ruta"],
    "pesos": { "distancia": 0.35, "especialidad": 0.25, "disponibilidad": 0.2, "carga": 0.1, "calificacion": 0.1 }
  },
  "total_evaluados": 22,
  "candidatos": [
    {
      "taller_id": 21, "nombre": "taller martinez",
      "distancia_km": 4.05,
      "mecanicos_total": 1, "mecanicos_disponibles": 1,
      "asignaciones_activas": 0, "calificacion": 5.0,
      "puntaje_total": 78.0,
      "desglose": { "distancia": 25.5, "especialidad": 12.5, "disponibilidad": 20.0, "carga": 10.0, "calificacion": 10.0 }
    }
  ],
  "seleccionado": { ...el primero de la lista... }
}
```

**Cómo funciona el puntaje (para que lo puedas explicar):**

| Criterio       | Peso | Cómo se calcula                                                   |
|----------      |------|-----------------                                                  |
| Distancia      | 35%  | Haversine incidente→taller. 1.0 pegado, 0.0 en el borde del radio |
| Especialidad   | 25%  | % de mecánicos del taller con especialidad relevante a la categoría |
| Disponibilidad | 20%  | % de mecánicos en estado "disponible"                               |
| Carga          | 10%  | 1 − (asignaciones activas / nº mecánicos) — penaliza talleres saturados |
| Calificación   | 10%  | calificación promedio del taller / 5                               |

El radio de búsqueda depende de la prioridad de la categoría (alta=30 km,
media=20, baja=15). Si **ningún** taller entra en el radio, se duplica
automáticamente (la política de "ampliar radio" de la ruta crítica).

---

## 5. Consumo de recursos — resumen para tu laptop

| Acción                            | RAM                     | Disco                      | ¿Cuándo?          |
|--------                           |-----                    |-------                     |----------         |
| Backend normal (sin tocar IA)     | +0 MB                   | 0                          | siempre           |
| Asignación inteligente            | +0 MB                   | 0                          | ya disponible     |
| Resumen por plantilla             | +0 MB                   | 0                          | ya disponible     |
| Instalar torch CPU + transformers | —                       | ~700 MB                    | cuando tú decidas |
| Primera clasificación de imagen   | +600 MB (queda cargado) | +600 MB (caché del modelo) | al usarla  |
| Instalar Ollama + gemma2:2b       | —                       | ~2 GB                      | opcional   |
| Generar resumen con Gemma         | ~2 GB (proceso de Ollama, se libera solo) | 0        | al usarlo  |

**Total de disco si instalas todo: ~3.3 GB** (tienes 10 GB libres → ok,
pero quedarás con ~6.7 GB; considera limpiar antes si puedes).

**Recomendación de uso en tu equipo:** no uses la clasificación de imágenes
y la generación con Gemma *al mismo tiempo* la primera vez. Prueba primero
una, verifica cuánta RAM te queda (Administrador de tareas), y luego la otra.

---

## 6. Solución de problemas

| Síntoma                                        | Causa                      | Solución                  |
|---------                                       |-------                     |----------                 |
| `503: Las librerías de IA no están instaladas` | Falta torch/transformers   | Sección 3, Parte A        |
| Primera clasificación tarda minutos            | Descargando CLIP (~600 MB) | Normal, solo pasa una vez |
| `modelo_usado: "plantilla (sin LLM)"` siempre  | Ollama no corre o no está instalado | `ollama serve` o instalar (Parte B); verifica con `GET /ia/estado` |
| Resumen con Gemma tarda >60 s y falla        | Timeout por RAM insuficiente | Cierra Chrome; o usa plantilla (cierra Ollama) |
| La laptop se congela al clasificar           | Sin RAM libre para cargar CLIP | Libera RAM antes; el modelo necesita ~600 MB |
| `candidatos: []` en asignación | Talleres sin coordenadas/mecánicos o muy lejos | Verifica que los talleres tengan lat/lng y mecánicos; el radio ya se amplía solo |
| El backend no arranca tras instalar torch      | Conflicto de versiones      | `pip install "numpy<2"` suele resolverlo |

---

## 7. Cómo encaja con el resto del sistema (ruta crítica)

- **Fase 1** (cliente reporta): el endpoint de clasificación puede ejecutarse
  sobre la foto del incidente (`incidente.foto_incidente` o sus evidencias),
  y el resumen llena `incidente.resumen_ia` — el campo que la web del admin
  ya puede mostrar. Cada ejecución queda auditada en `procesamientos_ia`.
- **Fase 2** (buscar talleres): `GET /ia/asignacion-inteligente/{id}` es
  exactamente el "motor de asignación" de la ruta crítica: filtra por
  especialidad, distancia, disponibilidad y devuelve el subconjunto de
  candidatos — listo para conectarlo al envío de notificaciones si después
  quieres automatizar la Fase 2 completa.
- **Bitácora**: las tres operaciones registran su acción
  (IA_CLASIFICAR_IMAGEN, IA_GENERAR_RESUMEN, IA_ASIGNACION_INTELIGENTE).

## 8. Ideas de siguiente paso (cuando todo esté instalado)

1. Botón "Analizar con IA" en la vista de Solicitudes disponibles (Angular)
   que llame a clasificar + resumen y muestre la ficha.
2. Llamar a la asignación inteligente automáticamente al crear un incidente
   y notificar solo a los talleres candidatos (Fase 2 completa).
3. Mostrar `resumen_ia` en la tarjeta del incidente en la app web y móvil.
