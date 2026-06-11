"""
reporte_qbe.py — Contrato JSON del módulo "Reportes Dinámicos por Prompts" (Fase 1).

Este es el JSON que en la Fase 2 generará el LLM (Structured Outputs) a partir
del texto del usuario. El backend NUNCA recibe SQL: solo esta estructura,
que el motor (services/qbe_engine.py) valida contra una whitelist.

Ejemplo de QBE "Gerencial" (detalle):
{
  "entidad": "pagos",
  "filtros": [{"campo": "estado", "operador": "igual", "valor": "pagado"}],
  "rango_fechas": {"campo": "fecha_pago", "desde": "2026-01-01", "hasta": "2026-03-31"},
  "orden": {"campo": "monto", "direccion": "desc"},
  "pagina": 1,
  "tamano_pagina": 50
}

Ejemplo de QBE "Ejecutivo" (agrupado):
{
  "entidad": "pagos",
  "rango_fechas": {"desde": "2026-01-01"},
  "group_by": ["metodo"],
  "agregaciones": [
    {"funcion": "sumar",  "campo": "monto", "alias": "ingresos"},
    {"funcion": "contar", "alias": "cantidad"}
  ],
  "orden": {"campo": "ingresos", "direccion": "desc"}
}
"""
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class OperadorFiltro(str, Enum):
    igual        = "igual"
    distinto     = "distinto"
    mayor_que    = "mayor_que"
    mayor_igual  = "mayor_igual"
    menor_que    = "menor_que"
    menor_igual  = "menor_igual"
    contiene     = "contiene"      # texto, case-insensitive
    empieza_con  = "empieza_con"
    en_lista     = "en_lista"      # valor debe ser una lista
    es_nulo      = "es_nulo"       # no requiere valor
    no_es_nulo   = "no_es_nulo"    # no requiere valor


class FuncionAgregacion(str, Enum):
    contar   = "contar"    # campo opcional (cuenta filas)
    sumar    = "sumar"
    promedio = "promedio"
    minimo   = "minimo"
    maximo   = "maximo"


class Filtro(BaseModel):
    campo: str
    operador: OperadorFiltro
    valor: Any = None


class RangoFechas(BaseModel):
    # Si no se indica campo, el motor usa el campo de fecha por defecto de la entidad
    campo: Optional[str] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None


class Orden(BaseModel):
    # En reportes agrupados también puede ser el alias de una agregación
    campo: str
    direccion: Literal["asc", "desc"] = "desc"


class Agregacion(BaseModel):
    funcion: FuncionAgregacion
    campo: Optional[str] = None        # obligatorio salvo para 'contar'
    alias: Optional[str] = None        # nombre de la columna en el resultado


class QBERequest(BaseModel):
    entidad: str
    filtros: list[Filtro] = []
    rango_fechas: Optional[RangoFechas] = None
    group_by: list[str] = []
    agregaciones: list[Agregacion] = []
    orden: Optional[Orden] = None
    pagina: int = Field(default=1, ge=1)
    tamano_pagina: int = Field(default=100, ge=1, le=1000)


class QBEResponse(BaseModel):
    entidad: str
    tipo_reporte: Literal["detalle", "agrupado"]
    total: int                       # total de filas SIN paginación
    pagina: int
    tamano_pagina: int
    columnas: list[str]
    filas: list[dict[str, Any]]
