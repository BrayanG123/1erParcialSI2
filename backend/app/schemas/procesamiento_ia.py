from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.procesamiento_ia import EstadoProcesamiento


class ProcesamientoIARead(BaseModel):
    id: int
    incidente_id: int
    estado: EstadoProcesamiento
    resumen_generado: Optional[str] = None
    mensaje_error: Optional[str] = None
    modelo_usado: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None

    model_config = {"from_attributes": True}