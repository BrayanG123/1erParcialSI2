from datetime import datetime
from pydantic import BaseModel

from app.models.evidencia import TipoEvidencia



class EvidenciaCreate(BaseModel):
    incidente_id: int
    tipo:         TipoEvidencia
    url_archivo:  str


class EvidenciaRead(BaseModel):
    id:           int
    incidente_id: int
    tipo:         TipoEvidencia
    url_archivo:  str
    procesado_ia: int
    fecha_subida: datetime

    model_config = {"from_attributes": True}