"""
kpi.py — Endpoints analíticos y de KPIs para el dashboard del administrador.

Todos los endpoints:
  - Requieren rol: administrador
  - Filtran automáticamente por el tenant_id del JWT del administrador
  - Aceptan filtros opcionales: fecha_desde, fecha_hasta, taller_id
  - Devuelven dicts (no modelos Pydantic) ya que son datos calculados, no entidades

Prefix: /kpi
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_administrador, require_tenant
from app.models.usuario import Usuario
from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.models.servicio_realizado import ServicioRealizado
from app.models.calificacion import Calificacion
from app.models.incidente import Incidente
from app.models.categoria import Categoria
from app.models.usuario import Mecanico
from app.models.taller import Taller
from app.models.pago import Pago, EstadoPago
from app.models.comision import Comision
from app.models.historial_estado import HistorialEstado



router = APIRouter(
    prefix="/kpi",
    tags=["KPIs"],
)

# ─────────────────────────────────────────────────────────────
# PARÁMETROS OPCIONALES COMUNES (reutilizados en varios endpoints)
# ─────────────────────────────────────────────────────────────
# Los definimos como funciones por las restricciones de FastAPI con Query defaults.


def _filtros_comunes(
    fecha_desde: Optional[datetime] = Query(
        None,
        description="Inicio del período (ISO 8601, ej: 2026-01-01T00:00:00)",
    ),
    fecha_hasta: Optional[datetime] = Query(
        None,
        description="Fin del período (ISO 8601, ej: 2026-12-31T23:59:59)",
    ),
    taller_id: Optional[int] = Query(
        None,
        description="Filtrar por taller específico (dentro del tenant)",
    ),
):
    return {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta, "taller_id": taller_id}



def _aplicar_filtros_a_query(query, filtros: dict, fecha_col=None, taller_join=False):
    """
    Aplica los filtros de fecha y taller a un query SQLAlchemy.

    - fecha_col: columna de fecha a filtrar (normalmente AsignacionServicio.fecha_creacion)
    - taller_join: si True, asume que ya hay un JOIN con mecanicos y talleres
    """
    if fecha_col is not None:
        if filtros["fecha_desde"]:
            query = query.filter(fecha_col >= filtros["fecha_desde"])
        if filtros["fecha_hasta"]:
            query = query.filter(fecha_col <= filtros["fecha_hasta"])
    if taller_join and filtros["taller_id"]:
        from app.models.usuario import Mecanico as MecanicoModel
        query = (
            query
            .join(MecanicoModel, MecanicoModel.id == AsignacionServicio.mecanico_id)
            .filter(MecanicoModel.taller_id == filtros["taller_id"])
        )
    return query




# ─────────────────────────────────────────────────────────────
# ENDPOINT 1 — Resumen general
# ─────────────────────────────────────────────────────────────

@router.get("/resumen")
def get_resumen(
    filtros: dict = Depends(_filtros_comunes),
    tenant_id: int = Depends(require_tenant),
    _usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Tarjetas principales del dashboard.

    Devuelve:
      - Conteo de asignaciones por estado (completadas, canceladas, en progreso)
      - Incidentes disponibles (sin asignar) — global, no filtrado por tenant
      - Ingresos totales (sum de pagos pagados del tenant)
      - Comisiones generadas
      - Calificación promedio de todos los servicios del tenant
    """
    # ── Base: asignaciones de este tenant ─────────────────────
    base = db.query(AsignacionServicio).filter(
        AsignacionServicio.tenant_id == tenant_id
    )
    base = _aplicar_filtros_a_query(
        base, filtros, fecha_col=AsignacionServicio.fecha_creacion
    )

    total_asignaciones = base.count()
    completadas  = base.filter(AsignacionServicio.estado == EstadoAsignacion.finalizado).count()
    canceladas   = base.filter(AsignacionServicio.estado == EstadoAsignacion.cancelado).count()
    rechazadas   = base.filter(AsignacionServicio.estado == EstadoAsignacion.rechazada).count()
    en_progreso  = total_asignaciones - completadas - canceladas - rechazadas

    # ── Incidentes disponibles (globales, sin asignar) ─────────
    disponibles = (
        db.query(Incidente)
        .filter(Incidente.estado == "disponible")
        .count()
    )

    # ── Ingresos: pagos pagados de servicios de este tenant ────
    ingresos_result = (
        db.query(func.coalesce(func.sum(Pago.monto), 0))
        .join(ServicioRealizado, ServicioRealizado.id == Pago.servicio_id)
        .filter(
            ServicioRealizado.tenant_id == tenant_id,
            Pago.estado == EstadoPago.pagado,
        )
        .scalar()
    )

    # ── Comisiones generadas ───────────────────────────────────
    comisiones_result = (
        db.query(func.coalesce(func.sum(Comision.monto), 0))
        .filter(Comision.tenant_id == tenant_id)
        .scalar()
    )

    # ── Calificación promedio ──────────────────────────────────
    calificacion_result = (
        db.query(func.avg(Calificacion.puntuacion))
        .join(ServicioRealizado, ServicioRealizado.id == Calificacion.servicio_id)
        .filter(ServicioRealizado.tenant_id == tenant_id)
        .scalar()
    )

    return {
        "total_asignaciones": total_asignaciones,
        "completadas":        completadas,
        "canceladas":         canceladas,
        "rechazadas":         rechazadas,
        "en_progreso":        en_progreso,
        "disponibles_sin_atender": disponibles,
        "ingresos_totales":   round(float(ingresos_result), 2),
        "comisiones_generadas": round(float(comisiones_result), 2),
        "calificacion_promedio": (
            round(float(calificacion_result), 2) if calificacion_result else None
        ),
    }



# ─────────────────────────────────────────────────────────────
# ENDPOINT 2 — Incidentes por tipo (categoría)
# ─────────────────────────────────────────────────────────────

@router.get("/incidentes-por-tipo")
def get_incidentes_por_tipo(
    filtros: dict = Depends(_filtros_comunes),
    tenant_id: int = Depends(require_tenant),
    _usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Distribución de incidentes por categoría — para gráfico de torta/pie.

    Devuelve lista ordenada de mayor a menor con porcentaje.
    """
    query = (
        db.query(
            Categoria.nombre.label("categoria"),
            func.count(AsignacionServicio.id).label("total"),
        )
        .join(Incidente, Incidente.id == AsignacionServicio.incidente_id)
        .join(Categoria, Categoria.id == Incidente.categoria_id)
        .filter(AsignacionServicio.tenant_id == tenant_id)
    )

    if filtros["fecha_desde"]:
        query = query.filter(AsignacionServicio.fecha_creacion >= filtros["fecha_desde"])
    if filtros["fecha_hasta"]:
        query = query.filter(AsignacionServicio.fecha_creacion <= filtros["fecha_hasta"])

    query = query.group_by(Categoria.nombre).order_by(func.count(AsignacionServicio.id).desc())
    rows = query.all()

    total_general = sum(r.total for r in rows) or 1  # evitar división por cero

    return [
        {
            "categoria": r.categoria,
            "total": r.total,
            "porcentaje": round(r.total * 100 / total_general, 1),
        }
        for r in rows
    ]



# ─────────────────────────────────────────────────────────────
# ENDPOINT 3 — Incidentes por fecha (serie temporal)
# ─────────────────────────────────────────────────────────────

@router.get("/incidentes-por-fecha")
def get_incidentes_por_fecha(
    filtros: dict = Depends(_filtros_comunes),
    tenant_id: int = Depends(require_tenant),
    _usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
    agrupacion: str = Query(
        "dia",
        description="Agrupar por: 'dia', 'semana' o 'mes'",
        pattern="^(dia|semana|mes)$",
    ),
):
    """
    Serie temporal de incidentes — para gráfico de línea.

    Retorna una lista de {fecha, total} ordenada cronológicamente.
    Útil para ver tendencias: ¿hay más incidentes los lunes? ¿en diciembre?
    """
    # Mapa del parámetro a la unidad de DATE_TRUNC
    unidad_sql = {"dia": "day", "semana": "week", "mes": "month"}[agrupacion]

    # Truncar la fecha a la granularidad elegida
    fecha_truncada = func.date_trunc(unidad_sql, AsignacionServicio.fecha_creacion)

    query = (
        db.query(
            fecha_truncada.label("fecha"),
            func.count(AsignacionServicio.id).label("total"),
        )
        .filter(AsignacionServicio.tenant_id == tenant_id)
    )

    if filtros["fecha_desde"]:
        query = query.filter(AsignacionServicio.fecha_creacion >= filtros["fecha_desde"])
    if filtros["fecha_hasta"]:
        query = query.filter(AsignacionServicio.fecha_creacion <= filtros["fecha_hasta"])

    rows = (
        query
        .group_by(fecha_truncada)
        .order_by(fecha_truncada)
        .all()
    )

    return [
        {
            "fecha": r.fecha.strftime("%Y-%m-%d") if r.fecha else None,
            "total": r.total,
        }
        for r in rows
    ]



# ─────────────────────────────────────────────────────────────
# ENDPOINT 4 — Tiempos promedio
# ─────────────────────────────────────────────────────────────

@router.get("/tiempos-promedio")
def get_tiempos_promedio(
    filtros: dict = Depends(_filtros_comunes),
    tenant_id: int = Depends(require_tenant),
    _usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Tiempos promedio del proceso de servicio (en minutos).

    - tiempo_asignacion_min: desde creación del incidente hasta que el admin acepta
    - tiempo_llegada_min: desde que el mecánico sale hasta que llega (taller_asignado → en_atencion)
    - tiempo_servicio_min: desde que atiende hasta que finaliza (en_atencion → finalizado)
    - tiempo_total_min: tiempo total desde creación hasta finalización

    Usa la tabla historial_estados para los tiempos intermedios.
    Solo cuenta asignaciones en estado 'finalizado'.
    """
    # Usamos text() porque EXTRACT(EPOCH FROM ...) con self-JOINs es más
    # claro en SQL puro que en SQLAlchemy ORM.
    sql = text("""
        SELECT
            -- Tiempo de asignación: creación → respuesta del admin
            ROUND(
                AVG(EXTRACT(EPOCH FROM (a.fecha_respuesta - a.fecha_creacion)) / 60)::numeric,
                1
            ) AS tiempo_asignacion_min,

            -- Tiempo de llegada: taller_asignado → en_atencion (via historial)
            ROUND(
                AVG(EXTRACT(EPOCH FROM (h_atencion.fecha_cambio - h_asignado.fecha_cambio)) / 60)::numeric,
                1
            ) AS tiempo_llegada_min,

            -- Tiempo de servicio: en_atencion → finalizado (via historial)
            ROUND(
                AVG(EXTRACT(EPOCH FROM (h_fin.fecha_cambio - h_atencion.fecha_cambio)) / 60)::numeric,
                1
            ) AS tiempo_servicio_min,

            -- Tiempo total: creación del incidente → finalización
            ROUND(
                AVG(EXTRACT(EPOCH FROM (h_fin.fecha_cambio - a.fecha_creacion)) / 60)::numeric,
                1
            ) AS tiempo_total_min,

            COUNT(a.id) AS total_servicios_medidos

        FROM asignaciones_servicio a

        -- JOIN hacia el estado 'taller_asignado'
        JOIN historial_estados h_asignado
            ON h_asignado.asignacion_id = a.id
            AND h_asignado.estado_actual = 'taller_asignado'

        -- JOIN hacia el estado 'en_atencion'
        JOIN historial_estados h_atencion
            ON h_atencion.asignacion_id = a.id
            AND h_atencion.estado_actual = 'en_atencion'

        -- JOIN hacia el estado 'finalizado'
        JOIN historial_estados h_fin
            ON h_fin.asignacion_id = a.id
            AND h_fin.estado_actual = 'finalizado'

        WHERE a.tenant_id = :tenant_id
          AND a.estado = 'finalizado'
          AND a.fecha_respuesta IS NOT NULL
          -- Filtros opcionales de fecha
          AND (:fecha_desde IS NULL OR a.fecha_creacion >= :fecha_desde)
          AND (:fecha_hasta IS NULL OR a.fecha_creacion <= :fecha_hasta)
    """)

    row = db.execute(sql, {
        "tenant_id":   tenant_id,
        "fecha_desde": filtros["fecha_desde"],
        "fecha_hasta": filtros["fecha_hasta"],
    }).fetchone()

    if not row or row.total_servicios_medidos == 0:
        return {
            "tiempo_asignacion_min":  None,
            "tiempo_llegada_min":     None,
            "tiempo_servicio_min":    None,
            "tiempo_total_min":       None,
            "total_servicios_medidos": 0,
            "nota": "No hay suficientes datos con historial completo en el período."
        }

    return {
        "tiempo_asignacion_min":   float(row.tiempo_asignacion_min or 0),
        "tiempo_llegada_min":      float(row.tiempo_llegada_min or 0),
        "tiempo_servicio_min":     float(row.tiempo_servicio_min or 0),
        "tiempo_total_min":        float(row.tiempo_total_min or 0),
        "total_servicios_medidos": row.total_servicios_medidos,
    }



# ─────────────────────────────────────────────────────────────
# ENDPOINT 5 — Ranking de talleres
# ─────────────────────────────────────────────────────────────

@router.get("/ranking-talleres")
def get_ranking_talleres(
    filtros: dict = Depends(_filtros_comunes),
    tenant_id: int = Depends(require_tenant),
    _usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Ranking de talleres por eficiencia.

    Ordena por servicios completados (desc). Incluye:
      - servicios_completados
      - calificacion_promedio
      - ingresos_totales
      - tiempo_respuesta_min (promedio)
    """
    sql = text("""
        SELECT
            t.id                          AS taller_id,
            t.nombre                      AS taller,
            COUNT(a.id)
                FILTER (WHERE a.estado = 'finalizado') AS servicios_completados,
            COUNT(a.id)
                FILTER (WHERE a.estado = 'cancelado')  AS servicios_cancelados,
            ROUND(AVG(c.puntuacion)::numeric, 2)        AS calificacion_promedio,
            ROUND(SUM(p.monto)::numeric, 2)             AS ingresos_totales,
            ROUND(
                AVG(EXTRACT(EPOCH FROM (a.fecha_respuesta - a.fecha_creacion)) / 60)
                FILTER (WHERE a.fecha_respuesta IS NOT NULL)
                ::numeric, 1
            )                                           AS tiempo_respuesta_min

        FROM talleres t
        JOIN mecanicos m    ON m.taller_id = t.id
        JOIN asignaciones_servicio a ON a.mecanico_id = m.id

        LEFT JOIN servicios_realizados sr ON sr.asignacion_id = a.id
        LEFT JOIN calificaciones c        ON c.servicio_id = sr.id
        LEFT JOIN pagos p
            ON p.servicio_id = sr.id AND p.estado = 'pagado'

        WHERE t.tenant_id = :tenant_id
          AND (:fecha_desde IS NULL OR a.fecha_creacion >= :fecha_desde)
          AND (:fecha_hasta IS NULL OR a.fecha_creacion <= :fecha_hasta)
          AND (:taller_id IS NULL   OR t.id = :taller_id)

        GROUP BY t.id, t.nombre
        ORDER BY servicios_completados DESC
        LIMIT 20
    """)

    rows = db.execute(sql, {
        "tenant_id":  tenant_id,
        "fecha_desde": filtros["fecha_desde"],
        "fecha_hasta": filtros["fecha_hasta"],
        "taller_id":  filtros["taller_id"],
    }).fetchall()

    return [
        {
            "taller_id":              row.taller_id,
            "taller":                 row.taller,
            "servicios_completados":  row.servicios_completados or 0,
            "servicios_cancelados":   row.servicios_cancelados or 0,
            "calificacion_promedio":  float(row.calificacion_promedio) if row.calificacion_promedio else None,
            "ingresos_totales":       float(row.ingresos_totales or 0),
            "tiempo_respuesta_min":   float(row.tiempo_respuesta_min) if row.tiempo_respuesta_min else None,
        }
        for row in rows
    ]



# ─────────────────────────────────────────────────────────────
# ENDPOINT 6 — Zonas con más incidentes
# ─────────────────────────────────────────────────────────────

@router.get("/zonas-incidentes")
def get_zonas_incidentes(
    filtros: dict = Depends(_filtros_comunes),
    tenant_id: int = Depends(require_tenant),
    _usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
    precision: int = Query(
        1,
        ge=0,
        le=3,
        description="Decimales de lat/lng para agrupar zonas. "
                    "0=ciudad entera, 1=zona (~11km), 2=barrio (~1km)",
    ),
):
    """
    Mapa de calor — zonas geográficas con más incidentes.

    Agrupa incidentes redondeando lat/lng a N decimales:
      precision=0 → grilla de ~111km (ciudad entera)
      precision=1 → grilla de ~11km (zona/barrio grande)
      precision=2 → grilla de ~1km  (barrio)

    Devuelve lista de {lat, lng, total} ordenada de mayor a menor densidad.
    Ideal para renderizar en un mapa como círculos de tamaño proporcional.
    """
    sql = text("""
        SELECT
            ROUND(CAST(i.latitud  AS numeric), :precision) AS lat,
            ROUND(CAST(i.longitud AS numeric), :precision) AS lng,
            COUNT(i.id)                                    AS total
        FROM incidentes i
        JOIN asignaciones_servicio a ON a.incidente_id = i.id
        WHERE a.tenant_id = :tenant_id
          AND i.latitud  IS NOT NULL
          AND i.longitud IS NOT NULL
          AND (:fecha_desde IS NULL OR a.fecha_creacion >= :fecha_desde)
          AND (:fecha_hasta IS NULL OR a.fecha_creacion <= :fecha_hasta)
        GROUP BY lat, lng
        ORDER BY total DESC
        LIMIT 50
    """)

    rows = db.execute(sql, {
        "tenant_id":  tenant_id,
        "precision":  precision,
        "fecha_desde": filtros["fecha_desde"],
        "fecha_hasta": filtros["fecha_hasta"],
    }).fetchall()

    return [
        {"lat": float(row.lat), "lng": float(row.lng), "total": row.total}
        for row in rows
    ]



# ─────────────────────────────────────────────────────────────
# ENDPOINT 7 — Cumplimiento de SLA
# ─────────────────────────────────────────────────────────────

@router.get("/sla")
def get_sla(
    filtros: dict = Depends(_filtros_comunes),
    tenant_id: int = Depends(require_tenant),
    _usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
    limite_horas: float = Query(
        3.0,
        ge=0.5,
        le=24.0,
        description="Tiempo máximo (horas) para completar un servicio y contar como 'dentro del SLA'.",
    ),
):
    """
    Cumplimiento del SLA (Service Level Agreement).

    El SLA se define como: el servicio debe completarse dentro de N horas
    desde que se creó el incidente.

    Por defecto: 3 horas.

    Retorna:
      - total_completados: servicios finalizados en el período
      - dentro_sla: cuántos se completaron a tiempo
      - fuera_sla: cuántos tardaron más
      - porcentaje_sla: % de cumplimiento
      - limite_horas: el límite usado para el cálculo
    """
    sql = text("""
        SELECT
            COUNT(a.id)  AS total_completados,
            COUNT(a.id) FILTER (
                WHERE EXTRACT(EPOCH FROM (sr.fecha_realizado - i.fecha_hora)) / 3600 <= :limite_horas
            )            AS dentro_sla
        FROM asignaciones_servicio a
        JOIN incidentes i            ON i.id  = a.incidente_id
        JOIN servicios_realizados sr ON sr.asignacion_id = a.id
        WHERE a.tenant_id = :tenant_id
          AND a.estado = 'finalizado'
          AND sr.fecha_realizado IS NOT NULL
          AND i.fecha_hora       IS NOT NULL
          AND (:fecha_desde IS NULL OR a.fecha_creacion >= :fecha_desde)
          AND (:fecha_hasta IS NULL OR a.fecha_creacion <= :fecha_hasta)
    """)

    row = db.execute(sql, {
        "tenant_id":    tenant_id,
        "limite_horas": limite_horas,
        "fecha_desde":  filtros["fecha_desde"],
        "fecha_hasta":  filtros["fecha_hasta"],
    }).fetchone()

    total       = row.total_completados or 0
    dentro      = row.dentro_sla or 0
    fuera       = total - dentro
    porcentaje  = round(dentro * 100 / total, 1) if total > 0 else 0.0

    return {
        "total_completados": total,
        "dentro_sla":        dentro,
        "fuera_sla":         fuera,
        "porcentaje_sla":    porcentaje,
        "limite_horas":      limite_horas,
    }