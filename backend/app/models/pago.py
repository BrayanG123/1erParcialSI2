import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, String, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base



class EstadoPago(str, enum.Enum):
    pendiente = "pendiente"
    pagado    = "pagado"


class MetodoPago(str, enum.Enum):
    efectivo       = "efectivo"
    pasarela       = "pasarela"
    # tarjeta        = "tarjeta"
    # qr             = "qr" #para despues


class Pago(Base):
    __tablename__ = "pagos"

    id             = Column(Integer, primary_key=True, index=True)
    monto          = Column(Float,   nullable=False)
    estado         = Column(
        SAEnum(EstadoPago, name="estado_pago"),
        default=EstadoPago.pendiente,
        nullable=False
    )
    metodo         = Column(
        SAEnum(MetodoPago, name="metodo_pago"),
        nullable=True
    )
    referencia     = Column(String(200), nullable=True)   # nro. de comprobante / transacción
    # observaciones  = Column(Text,        nullable=True)
    fecha_pago     = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Foreign Key (1:1 con ServicioRealizado) ---
    servicio_id = Column(
        Integer,
        ForeignKey("servicios_realizados.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    # --- Relación ---
    servicio = relationship("ServicioRealizado", back_populates="pago")