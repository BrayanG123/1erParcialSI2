"""
clasificador_imagen.py — Visión artificial para clasificar fotos de incidentes.

MODELO: CLIP ViT-B/32 (openai/clip-vit-base-patch32, ~600 MB en disco/RAM)

¿POR QUÉ CLIP?
  CLIP es un modelo "zero-shot": compara una imagen contra descripciones de
  texto y dice cuál se parece más. NO necesita re-entrenarse con fotos de
  autos — solo definimos buenas descripciones por categoría (abajo).
  Corre bien en CPU (2-4 segundos por imagen en un i5 8th gen).

USO DE MEMORIA (importante para tu laptop):
  - El modelo NO se carga al iniciar el backend.
  - Se carga la PRIMERA vez que alguien clasifica una imagen (~600 MB RAM)
    y queda en memoria para las siguientes (singleton).
  - Si no quieres ese consumo, simplemente no uses el endpoint.

REQUISITOS (ver requirements-ia.txt — NO vienen instalados por defecto):
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  pip install transformers pillow
"""
import io
import logging
import urllib.request

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# CATEGORÍAS Y SUS DESCRIPCIONES (prompts para CLIP)
#
# CLIP fue entrenado con texto en INGLÉS, por eso los prompts van en inglés.
# Cada categoría tiene varias descripciones: se promedian sus similitudes,
# lo que hace la clasificación más robusta.
# ─────────────────────────────────────────────────────────────

PROMPTS_POR_CATEGORIA: dict[str, list[str]] = {
    "bateria": [
        "a photo of a car with a dead battery being jump started",
        "a photo of a car battery under the hood of a car",
        "a photo of jumper cables connected to a car battery",
    ],
    "llanta": [
        "a photo of a car with a flat tire",
        "a photo of a punctured or deflated car tire",
        "a photo of someone changing a car wheel on the road",
    ],
    "choque": [
        "a photo of a car crash or collision with visible damage",
        "a photo of a dented or smashed car after an accident",
        "a photo of two vehicles that collided on the street",
    ],
    "motor": [
        "a photo of a car engine with smoke coming out",
        "a photo of an overheated car engine with the hood open",
        "a photo of a broken car engine being repaired",
    ],
    "otros": [
        "a photo of a car parked on the road with no visible damage",
        "a photo of a generic vehicle problem",
        "a photo of a car interior or dashboard",
    ],
}

# Mapeo de la categoría IA → nombre (parcial) de la Categoria en la BD.
# Se usa para actualizar incidente.categoria_id automáticamente.
CATEGORIA_IA_A_BD: dict[str, str] = {
    "bateria": "Batería",
    "llanta":  "Llanta",
    "choque":  "Choque",
    "motor":   "Motor",
    # "otros" no se mapea: se deja la categoría que eligió el cliente
}

# Prioridad sugerida por categoría (1=baja, 2=media, 3=alta)
PRIORIDAD_POR_CATEGORIA: dict[str, int] = {
    "choque": 3,
    "motor":  2,
    "bateria": 1,
    "llanta": 1,
    "otros":  1,
}

# ─────────────────────────────────────────────────────────────
# CARGA PEREZOSA DEL MODELO (singleton)
# ─────────────────────────────────────────────────────────────

# Variables globales del módulo: guardan el modelo una vez cargado
_modelo = None
_procesador = None

NOMBRE_MODELO = "openai/clip-vit-base-patch32"


def dependencias_instaladas() -> bool:
    """True si torch + transformers + pillow están instalados (sin cargarlos)."""
    import importlib.util
    return all(
        importlib.util.find_spec(paquete) is not None
        for paquete in ("torch", "transformers", "PIL")
    )


def _cargar_modelo():
    """
    Carga CLIP en memoria UNA sola vez (patrón singleton).
    La primera llamada descarga ~600 MB a la caché de HuggingFace
    (C:/Users/<usuario>/.cache/huggingface) si no existe.
    """
    global _modelo, _procesador
    if _modelo is not None:
        return  # ya está cargado

    if not dependencias_instaladas():
        raise RuntimeError(
            "Las librerías de IA no están instaladas. Ejecuta:\n"
            "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
            "  pip install transformers pillow\n"
            "(ver requirements-ia.txt y MODULO-IA.md)"
        )

    # Los imports van AQUÍ (no arriba) para que el backend arranque
    # aunque torch/transformers no estén instalados.
    from transformers import CLIPModel, CLIPProcessor

    logger.info(f"[IA] Cargando modelo {NOMBRE_MODELO} (primera vez, puede tardar)...")
    _modelo = CLIPModel.from_pretrained(NOMBRE_MODELO)
    _procesador = CLIPProcessor.from_pretrained(NOMBRE_MODELO)
    _modelo.eval()  # modo inferencia (desactiva dropout, etc.)
    logger.info("[IA] Modelo CLIP cargado correctamente.")


def modelo_cargado() -> bool:
    """True si CLIP ya está en memoria."""
    return _modelo is not None


# ─────────────────────────────────────────────────────────────
# CLASIFICACIÓN
# ─────────────────────────────────────────────────────────────

def _descargar_imagen(url: str) -> bytes:
    """Descarga una imagen desde una URL (ej: Cloudinary) y devuelve sus bytes."""
    with urllib.request.urlopen(url, timeout=20) as respuesta:
        return respuesta.read()


def clasificar_imagen(imagen_bytes: bytes = None, imagen_url: str = None) -> dict:
    """
    Clasifica la foto de un incidente en: bateria / llanta / choque / motor / otros.

    Parámetros (usar UNO de los dos):
        imagen_bytes : contenido binario de la imagen (upload directo)
        imagen_url   : URL de la imagen (ej: evidencia en Cloudinary)

    Retorna:
        {
          "categoria": "llanta",
          "confianza": 0.87,                 # probabilidad de la ganadora
          "prioridad_sugerida": 1,
          "puntuaciones": {"llanta": 0.87, "choque": 0.06, ...},
          "modelo": "openai/clip-vit-base-patch32"
        }
    """
    _cargar_modelo()  # carga perezosa (solo la primera vez)

    import torch
    from PIL import Image

    # 1. Obtener la imagen
    if imagen_bytes is None and imagen_url:
        imagen_bytes = _descargar_imagen(imagen_url)
    if not imagen_bytes:
        raise ValueError("Debes proporcionar imagen_bytes o imagen_url")

    imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")

    # 2. Aplanar los prompts: lista de textos + a qué categoría pertenece cada uno
    textos: list[str] = []
    categorias_de_texto: list[str] = []
    for categoria, prompts in PROMPTS_POR_CATEGORIA.items():
        for p in prompts:
            textos.append(p)
            categorias_de_texto.append(categoria)

    # 3. Pasar imagen + textos por CLIP
    #    CLIP devuelve un puntaje de similitud imagen↔texto por cada prompt
    entradas = _procesador(
        text=textos, images=imagen, return_tensors="pt", padding=True
    )
    with torch.no_grad():  # sin gradientes = menos RAM y más rápido
        salida = _modelo(**entradas)
        # softmax sobre todos los prompts → probabilidades que suman 1
        probabilidades = salida.logits_per_image.softmax(dim=1)[0]

    # 4. Sumar las probabilidades de los prompts de cada categoría
    puntuaciones: dict[str, float] = {c: 0.0 for c in PROMPTS_POR_CATEGORIA}
    for prob, categoria in zip(probabilidades.tolist(), categorias_de_texto):
        puntuaciones[categoria] += prob

    # 5. La categoría ganadora es la de mayor probabilidad acumulada
    categoria_ganadora = max(puntuaciones, key=puntuaciones.get)

    return {
        "categoria": categoria_ganadora,
        "confianza": round(puntuaciones[categoria_ganadora], 4),
        "prioridad_sugerida": PRIORIDAD_POR_CATEGORIA.get(categoria_ganadora, 1),
        "puntuaciones": {c: round(p, 4) for c, p in sorted(
            puntuaciones.items(), key=lambda x: -x[1]
        )},
        "modelo": NOMBRE_MODELO,
    }
