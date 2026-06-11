"""
asignador_inteligente.py — Selección del mejor taller para un incidente.

Este motor NO usa un modelo de IA pesado: es un algoritmo de puntuación
multi-criterio (lo correcto para este problema — determinista, explicable
y consume 0 MB de RAM extra, ideal para tu hardware).

CRITERIOS (los que pide el enunciado del módulo):
  1. Ubicación / distancia  → fórmula de Haversine entre incidente y taller
  2. Tipo de problema       → % de mecánicos con la especialidad adecuada
  3. Disponibilidad         → mecánicos en estado "disponible"
  4. Capacidad / carga      → asignaciones activas vs nº de mecánicos
  5. Prioridad del caso     → ajusta el radio de búsqueda y los pesos
  6. Calificación del taller → bonus de reputación

SALIDA: lista de talleres candidatos con el desglose de su puntaje,
ordenados de mejor a peor, y el seleccionado (el primero).
"""
import math

from sqlalchemy.orm import Session

from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.models.taller import Taller
from app.models.usuario import Mecanico

# ─────────────────────────────────────────────────────────────
# Configuración del algoritmo
# ─────────────────────────────────────────────────────────────

# Especialidades de mecánico relevantes por categoría de incidente.
# (las especialidades existentes en el sistema están en el seeder)
ESPECIALIDADES_POR_CATEGORIA: dict[str, list[str]] = {
    "batería":     ["sistema eléctrico", "diagnóstico general", "auxilio en ruta"],
    "eléctrico":   ["sistema eléctrico", "diagnóstico general"],
    "llanta":      ["llantas y suspensión", "auxilio en ruta"],
    "motor":       ["motor y transmisión", "diagnóstico general"],
    "choque":      ["chapería y pintura", "frenos y dirección"],
    "accidente":   ["chapería y pintura", "auxilio en ruta"],
    "combustible": ["auxilio en ruta", "diagnóstico general"],
    "frenos":      ["frenos y dirección", "diagnóstico general"],
}

# Pesos de cada criterio (suman 1.0)
PESOS = {
    "distancia":     0.35,   # el más importante: que llegue rápido
    "especialidad":  0.25,   # que sepa resolver el problema
    "disponibilidad": 0.20,  # que tenga mecánicos libres AHORA
    "carga":         0.10,   # que no esté saturado
    "calificacion":  0.10,   # reputación del taller
}

# Radio máximo de búsqueda según prioridad de la categoría (km)
RADIO_POR_PRIORIDAD = {3: 30.0, 2: 20.0, 1: 15.0}

# Estados de asignación que cuentan como "trabajo activo" del taller
_ESTADOS_ACTIVOS = (
    EstadoAsignacion.pendiente,
    EstadoAsignacion.taller_asignado,
    EstadoAsignacion.en_camino,
    EstadoAsignacion.en_atencion,
)


# ─────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────

def distancia_haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Distancia en línea recta (km) entre dos coordenadas GPS.
    Fórmula de Haversine: estándar para distancias sobre la esfera terrestre.
    """
    R = 6371.0  # radio de la Tierra en km
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _especialidades_relevantes(nombre_categoria: str) -> list[str]:
    """Devuelve las especialidades útiles para la categoría del incidente."""
    nombre = (nombre_categoria or "").lower()
    for clave, especialidades in ESPECIALIDADES_POR_CATEGORIA.items():
        if clave in nombre:
            return especialidades
    return []  # categoría desconocida: el criterio de especialidad será neutro


# ─────────────────────────────────────────────────────────────
# Evaluación de un taller
# ─────────────────────────────────────────────────────────────

def _evaluar_taller(
    db: Session,
    taller: Taller,
    incidente,
    especialidades: list[str],
    radio_km: float,
) -> dict | None:
    """
    Calcula el puntaje (0-100) de UN taller para el incidente.
    Devuelve None si el taller queda descartado (sin ubicación,
    fuera de radio o sin mecánicos).
    """
    # ── Descarte: el taller necesita coordenadas ──
    if taller.latitud is None or taller.longitud is None:
        return None

    # ── Criterio 1: distancia ──
    dist = distancia_haversine_km(
        incidente.latitud, incidente.longitud, taller.latitud, taller.longitud
    )
    if dist > radio_km:
        return None  # fuera del radio de búsqueda
    # 1.0 si está al lado, 0.0 si está en el borde del radio
    puntaje_distancia = 1.0 - (dist / radio_km)

    # ── Datos de los mecánicos del taller ──
    mecanicos = db.query(Mecanico).filter(Mecanico.taller_id == taller.id).all()
    if not mecanicos:
        return None  # un taller sin mecánicos no puede atender

    total_mecanicos = len(mecanicos)
    disponibles = [m for m in mecanicos if (m.estado or "").lower() == "disponible"]

    # ── Criterio 2: especialidad ──
    # Un mecánico puede tener VARIAS especialidades (separadas por comas);
    # cuenta si AL MENOS UNA coincide con las relevantes para la categoría.
    if especialidades:
        con_especialidad = sum(
            1 for m in mecanicos
            if any(e.lower() in especialidades for e in m.especialidades)
        )
        puntaje_especialidad = con_especialidad / total_mecanicos
    else:
        puntaje_especialidad = 0.5  # neutro si la categoría no mapea

    # ── Criterio 3: disponibilidad ──
    puntaje_disponibilidad = len(disponibles) / total_mecanicos

    # ── Criterio 4: carga de trabajo (asignaciones activas del taller) ──
    ids_mecanicos = [m.id for m in mecanicos]
    activas = (
        db.query(AsignacionServicio)
        .filter(
            AsignacionServicio.mecanico_id.in_(ids_mecanicos),
            AsignacionServicio.estado.in_(_ESTADOS_ACTIVOS),
        )
        .count()
    )
    # 0 activas = 1.0 | tantas activas como mecánicos (o más) = 0.0
    puntaje_carga = max(0.0, 1.0 - (activas / total_mecanicos))

    # ── Criterio 5: calificación (0-5 → 0-1) ──
    puntaje_calificacion = (taller.calificacion_promedio or 0.0) / 5.0

    # ── Puntaje final ponderado (0-100) ──
    puntaje = 100 * (
        PESOS["distancia"] * puntaje_distancia
        + PESOS["especialidad"] * puntaje_especialidad
        + PESOS["disponibilidad"] * puntaje_disponibilidad
        + PESOS["carga"] * puntaje_carga
        + PESOS["calificacion"] * puntaje_calificacion
    )

    return {
        "taller_id": taller.id,
        "nombre": taller.nombre,
        "direccion": taller.direccion,
        "telefono": taller.telefono,
        "distancia_km": round(dist, 2),
        "mecanicos_total": total_mecanicos,
        "mecanicos_disponibles": len(disponibles),
        "asignaciones_activas": activas,
        "calificacion": taller.calificacion_promedio,
        "puntaje_total": round(puntaje, 1),
        # Desglose para que el resultado sea EXPLICABLE:
        "desglose": {
            "distancia":      round(100 * PESOS["distancia"] * puntaje_distancia, 1),
            "especialidad":   round(100 * PESOS["especialidad"] * puntaje_especialidad, 1),
            "disponibilidad": round(100 * PESOS["disponibilidad"] * puntaje_disponibilidad, 1),
            "carga":          round(100 * PESOS["carga"] * puntaje_carga, 1),
            "calificacion":   round(100 * PESOS["calificacion"] * puntaje_calificacion, 1),
        },
    }


# ─────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────

def asignar_taller_inteligente(db: Session, incidente, top: int = 5) -> dict:
    """
    Evalúa TODOS los talleres activos contra el incidente y devuelve:
      - los criterios usados (radio, especialidades, prioridad)
      - la lista de candidatos ordenada por puntaje (máx `top`)
      - el taller seleccionado (el de mayor puntaje), o None si no hay

    Si ningún taller entra en el radio inicial, amplía el radio x2
    (igual que la "Fase 2" de la ruta crítica: relajar filtros).
    """
    categoria = incidente.categoria.nombre if incidente.categoria else ""
    prioridad = incidente.categoria.prioridad if incidente.categoria else 1
    especialidades = _especialidades_relevantes(categoria)
    radio = RADIO_POR_PRIORIDAD.get(prioridad, 15.0)

    talleres = db.query(Taller).filter(Taller.is_active == True).all()  # noqa: E712

    def evaluar_con_radio(r: float) -> list[dict]:
        resultados = []
        for taller in talleres:
            evaluacion = _evaluar_taller(db, taller, incidente, especialidades, r)
            if evaluacion:
                resultados.append(evaluacion)
        return sorted(resultados, key=lambda x: -x["puntaje_total"])

    candidatos = evaluar_con_radio(radio)
    radio_usado = radio

    # Sin candidatos → ampliar el radio (política de la ruta crítica)
    if not candidatos:
        radio_usado = radio * 2
        candidatos = evaluar_con_radio(radio_usado)

    return {
        "incidente_id": incidente.id,
        "criterios": {
            "categoria": categoria or "Sin categoría",
            "prioridad": prioridad,
            "radio_busqueda_km": radio_usado,
            "radio_ampliado": radio_usado != radio,
            "especialidades_buscadas": especialidades,
            "pesos": PESOS,
        },
        "total_evaluados": len(talleres),
        "candidatos": candidatos[:top],
        "seleccionado": candidatos[0] if candidatos else None,
    }
