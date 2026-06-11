"""
reporte_dinamico.py — Endpoints del módulo "Reportes Dinámicos por Prompts".

Fase 1 (actual): el cliente envía el JSON QBE directamente.
Fase 2 (futura): un endpoint adicional recibirá texto en lenguaje natural,
lo pasará al LLM (Structured Outputs) y el JSON resultante entrará por el
mismo motor ejecutar_qbe() — por eso el motor vive en services/, no aquí.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_administrador
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.reporte_qbe import QBERequest, QBEResponse
from app.services.qbe_engine import describir_esquema, ejecutar_qbe

router = APIRouter(prefix="/reportes", tags=["Reportes Dinámicos"])


@router.post("/qbe", response_model=QBEResponse)
def generar_reporte_qbe(
    qbe: QBERequest,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Ejecuta un reporte dinámico a partir de una estructura QBE.

    - Reporte GERENCIAL (detalle): sin group_by/agregaciones → filas individuales.
    - Reporte EJECUTIVO (agrupado): con group_by + agregaciones → totales por grupo.

    Toda consulta queda aislada al tenant del administrador autenticado.
    """
    tenant_id = usuario.perfil_administrador.tenant_id
    return ejecutar_qbe(db, qbe, tenant_id)


@router.get("/qbe/esquema")
def obtener_esquema_qbe(
    usuario: Usuario = Depends(get_current_administrador),
):
    """
    Catálogo de entidades, campos, operadores y agregaciones disponibles.
    En la Fase 2 este mismo esquema se inyectará al prompt del LLM.
    """
    return describir_esquema()
