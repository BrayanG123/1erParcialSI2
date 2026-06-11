"""
qbe_engine.py — Motor QBE (Query by Example) seguro. Fase 1 de Reportes Dinámicos.

Seguridad — el JSON del QBE (que en Fase 2 generará un LLM) JAMÁS toca SQL crudo:
  1. WHITELIST de entidades: solo las registradas en ENTIDADES.
  2. WHITELIST de campos: cada entidad expone solo los campos listados; un campo
     fuera de la lista → HTTP 400 (nunca getattr dinámico sobre el modelo).
  3. Operadores cerrados (Enum): se traducen a expresiones SQLAlchemy parametrizadas,
     por lo que los valores viajan como bind params (sin inyección SQL).
  4. Multi-tenant: toda consulta se filtra automáticamente por el tenant del admin.
     Las entidades sin tenant_id propio (pagos, calificaciones) lo heredan vía JOIN.
  5. Paginación con tope (máx 1000 filas) para proteger la BD.
"""
from typing import Any

from fastapi import HTTPException
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from app.models.asignacion_servicio import AsignacionServicio
from app.models.calificacion import Calificacion
from app.models.comision import Comision
from app.models.incidente import Incidente
from app.models.pago import Pago
from app.models.servicio_realizado import ServicioRealizado
from app.models.taller import Taller
from app.models.usuario import Mecanico
from app.schemas.reporte_qbe import (
    Agregacion,
    Filtro,
    FuncionAgregacion,
    OperadorFiltro,
    QBERequest,
)


# ─────────────────────────────────────────────────────────────
# REGISTRO DE ENTIDADES (la única "superficie" que el QBE puede tocar)
#
#   modelo        → clase SQLAlchemy base de la consulta
#   campos        → {nombre_expuesto: Column} whitelist de campos consultables
#   fecha_defecto → campo usado por rango_fechas si el QBE no indica uno
#   tenant_col    → columna para el filtro multi-tenant (None = entidad global)
#   joins         → modelos a JOINear antes de filtrar (para heredar tenant)
# ─────────────────────────────────────────────────────────────

ENTIDADES: dict[str, dict] = {
    "incidentes": {
        "modelo": Incidente,
        "campos": {
            "id": Incidente.id,
            "descripcion": Incidente.descripcion,
            "estado": Incidente.estado,
            "fecha_hora": Incidente.fecha_hora,
            "latitud": Incidente.latitud,
            "longitud": Incidente.longitud,
            "cliente_id": Incidente.cliente_id,
            "categoria_id": Incidente.categoria_id,
        },
        "fecha_defecto": "fecha_hora",
        "tenant_col": None,   # los incidentes son globales (del cliente)
        "joins": [],
    },
    "asignaciones": {
        "modelo": AsignacionServicio,
        "campos": {
            "id": AsignacionServicio.id,
            "estado": AsignacionServicio.estado,
            "costo_estimado": AsignacionServicio.costo_estimado,
            "distancia_km": AsignacionServicio.distancia_km,
            "tiempo_estimado": AsignacionServicio.tiempo_estimado,
            "fecha_creacion": AsignacionServicio.fecha_creacion,
            "fecha_respuesta": AsignacionServicio.fecha_respuesta,
            "motivo_rechazo": AsignacionServicio.motivo_rechazo,
            "incidente_id": AsignacionServicio.incidente_id,
            "mecanico_id": AsignacionServicio.mecanico_id,
        },
        "fecha_defecto": "fecha_creacion",
        "tenant_col": AsignacionServicio.tenant_id,
        "joins": [],
    },
    "servicios": {
        "modelo": ServicioRealizado,
        "campos": {
            "id": ServicioRealizado.id,
            "tipo_servicio": ServicioRealizado.tipo_servicio,
            "descripcion_trabajo": ServicioRealizado.descripcion_trabajo,
            "costo_final": ServicioRealizado.costo_final,
            "fecha_realizado": ServicioRealizado.fecha_realizado,
            "asignacion_id": ServicioRealizado.asignacion_id,
        },
        "fecha_defecto": "fecha_realizado",
        "tenant_col": ServicioRealizado.tenant_id,
        "joins": [],
    },
    "pagos": {
        "modelo": Pago,
        "campos": {
            "id": Pago.id,
            "monto": Pago.monto,
            "estado": Pago.estado,
            "metodo": Pago.metodo,
            "referencia": Pago.referencia,
            "fecha_pago": Pago.fecha_pago,
            "servicio_id": Pago.servicio_id,
            "tipo_servicio": ServicioRealizado.tipo_servicio,  # campo del JOIN
        },
        "fecha_defecto": "fecha_pago",
        # Pago no tiene tenant_id: lo hereda del servicio realizado
        "tenant_col": ServicioRealizado.tenant_id,
        "joins": [ServicioRealizado],
    },
    "comisiones": {
        "modelo": Comision,
        "campos": {
            "id": Comision.id,
            "porcentaje": Comision.porcentaje,
            "monto": Comision.monto,
            "fecha_emision": Comision.fecha_emision,
            "fecha_pago": Comision.fecha_pago,
            "servicio_id": Comision.servicio_id,
        },
        "fecha_defecto": "fecha_emision",
        "tenant_col": Comision.tenant_id,
        "joins": [],
    },
    "calificaciones": {
        "modelo": Calificacion,
        "campos": {
            "id": Calificacion.id,
            "puntuacion": Calificacion.puntuacion,
            "comentario": Calificacion.comentario,
            "fecha": Calificacion.fecha,
            "servicio_id": Calificacion.servicio_id,
            "tipo_servicio": ServicioRealizado.tipo_servicio,  # campo del JOIN
        },
        "fecha_defecto": "fecha",
        # Calificacion no tiene tenant_id: lo hereda del servicio
        "tenant_col": ServicioRealizado.tenant_id,
        "joins": [ServicioRealizado],
    },
    "mecanicos": {
        "modelo": Mecanico,
        "campos": {
            "id": Mecanico.id,
            "especialidad": Mecanico.especialidad,
            "estado": Mecanico.estado,
            "telefono": Mecanico.telefono,
            "taller_id": Mecanico.taller_id,
        },
        "fecha_defecto": None,
        "tenant_col": Mecanico.tenant_id,
        "joins": [],
    },
    "talleres": {
        "modelo": Taller,
        "campos": {
            "id": Taller.id,
            "nombre": Taller.nombre,
            "direccion": Taller.direccion,
            "telefono": Taller.telefono,
            "calificacion_promedio": Taller.calificacion_promedio,
            "is_active": Taller.is_active,
        },
        "fecha_defecto": None,
        "tenant_col": Taller.tenant_id,
        "joins": [],
    },
}

_FUNCIONES_AGG = {
    FuncionAgregacion.sumar: func.sum,
    FuncionAgregacion.promedio: func.avg,
    FuncionAgregacion.minimo: func.min,
    FuncionAgregacion.maximo: func.max,
}

# Operadores que exigen un valor no nulo
_REQUIEREN_VALOR = {
    OperadorFiltro.igual, OperadorFiltro.distinto,
    OperadorFiltro.mayor_que, OperadorFiltro.mayor_igual,
    OperadorFiltro.menor_que, OperadorFiltro.menor_igual,
    OperadorFiltro.contiene, OperadorFiltro.empieza_con,
    OperadorFiltro.en_lista,
}


# ─────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────

def _error(msg: str) -> HTTPException:
    return HTTPException(status_code=400, detail=msg)


def _config_entidad(entidad: str) -> dict:
    cfg = ENTIDADES.get(entidad)
    if not cfg:
        raise _error(
            f"Entidad '{entidad}' no permitida. "
            f"Entidades válidas: {sorted(ENTIDADES.keys())}"
        )
    return cfg


def _columna(cfg: dict, entidad: str, campo: str):
    """Resuelve un nombre de campo contra la whitelist. Nunca usa getattr dinámico."""
    col = cfg["campos"].get(campo)
    if col is None:
        raise _error(
            f"Campo '{campo}' no permitido para '{entidad}'. "
            f"Campos válidos: {sorted(cfg['campos'].keys())}"
        )
    return col


def _condicion(col, filtro: Filtro):
    """Traduce un Filtro del QBE a una expresión SQLAlchemy parametrizada."""
    op, valor = filtro.operador, filtro.valor

    if op in _REQUIEREN_VALOR and valor is None:
        raise _error(f"El operador '{op.value}' requiere un valor (campo '{filtro.campo}')")

    if op == OperadorFiltro.igual:
        return col == valor
    if op == OperadorFiltro.distinto:
        return col != valor
    if op == OperadorFiltro.mayor_que:
        return col > valor
    if op == OperadorFiltro.mayor_igual:
        return col >= valor
    if op == OperadorFiltro.menor_que:
        return col < valor
    if op == OperadorFiltro.menor_igual:
        return col <= valor
    if op == OperadorFiltro.contiene:
        return col.ilike(f"%{valor}%")
    if op == OperadorFiltro.empieza_con:
        return col.ilike(f"{valor}%")
    if op == OperadorFiltro.en_lista:
        if not isinstance(valor, list) or not valor:
            raise _error(f"'en_lista' requiere una lista no vacía (campo '{filtro.campo}')")
        return col.in_(valor)
    if op == OperadorFiltro.es_nulo:
        return col.is_(None)
    if op == OperadorFiltro.no_es_nulo:
        return col.isnot(None)

    raise _error(f"Operador '{op}' no soportado")  # inalcanzable (Enum cerrado)


def _expr_agregacion(cfg: dict, entidad: str, ag: Agregacion):
    """Construye la expresión de agregación y su alias."""
    alias = ag.alias or f"{ag.funcion.value}_{ag.campo or 'registros'}"

    if ag.funcion == FuncionAgregacion.contar:
        col = _columna(cfg, entidad, ag.campo) if ag.campo else cfg["modelo"].id
        return func.count(col).label(alias), alias

    if not ag.campo:
        raise _error(f"La agregación '{ag.funcion.value}' requiere un campo")
    return _FUNCIONES_AGG[ag.funcion](_columna(cfg, entidad, ag.campo)).label(alias), alias


# ─────────────────────────────────────────────────────────────
# API pública del motor
# ─────────────────────────────────────────────────────────────

def ejecutar_qbe(db: Session, qbe: QBERequest, tenant_id: int | None) -> dict:
    """
    Ejecuta un QBE validado y devuelve el dict listo para QBEResponse.
    tenant_id: tenant del admin autenticado (None = sin restricción, p.ej. superadmin).
    """
    cfg = _config_entidad(qbe.entidad)
    es_agrupado = bool(qbe.group_by or qbe.agregaciones)

    # ── SELECT ────────────────────────────────────────────────
    alias_agregaciones: set[str] = set()
    if es_agrupado:
        if not qbe.agregaciones:
            raise _error("Un reporte agrupado requiere al menos una agregación")
        select_cols = [
            _columna(cfg, qbe.entidad, g).label(g) for g in qbe.group_by
        ]
        for ag in qbe.agregaciones:
            expr, alias = _expr_agregacion(cfg, qbe.entidad, ag)
            select_cols.append(expr)
            alias_agregaciones.add(alias)
        # nombres en el orden real de las columnas seleccionadas
        columnas = [c.name for c in select_cols]
    else:
        select_cols = [col.label(nombre) for nombre, col in cfg["campos"].items()]
        columnas = list(cfg["campos"].keys())

    q = db.query(*select_cols)

    # ── JOINs + aislamiento multi-tenant ──────────────────────
    for modelo_join in cfg["joins"]:
        q = q.join(modelo_join)
    if tenant_id is not None and cfg["tenant_col"] is not None:
        q = q.filter(cfg["tenant_col"] == tenant_id)

    # ── Filtros ───────────────────────────────────────────────
    for f in qbe.filtros:
        q = q.filter(_condicion(_columna(cfg, qbe.entidad, f.campo), f))

    # ── Rango de fechas ───────────────────────────────────────
    if qbe.rango_fechas and (qbe.rango_fechas.desde or qbe.rango_fechas.hasta):
        nombre_campo = qbe.rango_fechas.campo or cfg["fecha_defecto"]
        if not nombre_campo:
            raise _error(
                f"La entidad '{qbe.entidad}' no tiene campo de fecha por defecto: "
                f"indica 'rango_fechas.campo' explícitamente"
            )
        col_fecha = _columna(cfg, qbe.entidad, nombre_campo)
        if qbe.rango_fechas.desde:
            q = q.filter(col_fecha >= qbe.rango_fechas.desde)
        if qbe.rango_fechas.hasta:
            q = q.filter(col_fecha <= qbe.rango_fechas.hasta)

    # ── GROUP BY ──────────────────────────────────────────────
    if es_agrupado:
        for g in qbe.group_by:
            q = q.group_by(_columna(cfg, qbe.entidad, g))

    # ── Total (antes de paginar) ──────────────────────────────
    # .count() envuelve la query en un subselect, así que también es
    # correcto para reportes agrupados (cuenta los grupos).
    total = q.count()

    # ── ORDER BY ──────────────────────────────────────────────
    if qbe.orden:
        if qbe.orden.campo in alias_agregaciones:
            # ordenar por el alias de una agregación (ej: "ingresos")
            orden_expr = next(
                c for c in select_cols if c.name == qbe.orden.campo
            )
        else:
            orden_expr = _columna(cfg, qbe.entidad, qbe.orden.campo)
        q = q.order_by(
            asc(orden_expr) if qbe.orden.direccion == "asc" else desc(orden_expr)
        )

    # ── Paginación ────────────────────────────────────────────
    offset = (qbe.pagina - 1) * qbe.tamano_pagina
    rows = q.offset(offset).limit(qbe.tamano_pagina).all()

    filas: list[dict[str, Any]] = [dict(r._mapping) for r in rows]

    return {
        "entidad": qbe.entidad,
        "tipo_reporte": "agrupado" if es_agrupado else "detalle",
        "total": total,
        "pagina": qbe.pagina,
        "tamano_pagina": qbe.tamano_pagina,
        "columnas": columnas,
        "filas": filas,
    }


def describir_esquema() -> dict:
    """
    Devuelve el "mapa" de entidades, campos y operadores disponibles.
    Uso doble:
      - El frontend puede construir UI de filtros.
      - En la Fase 2, este esquema se inyecta al prompt del LLM para que
        genere QBEs válidos (sabe exactamente qué entidades/campos existen).
    """
    return {
        "entidades": {
            nombre: {
                "campos": sorted(cfg["campos"].keys()),
                "fecha_defecto": cfg["fecha_defecto"],
            }
            for nombre, cfg in ENTIDADES.items()
        },
        "operadores": [op.value for op in OperadorFiltro],
        "agregaciones": [fn.value for fn in FuncionAgregacion],
        "limites": {"tamano_pagina_max": 1000},
    }
