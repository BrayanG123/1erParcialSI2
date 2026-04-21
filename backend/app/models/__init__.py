from app.models.base import Base
from app.models.usuario import Usuario, Cliente, Mecanico, Administrador, RolUsuario
from app.models.vehiculo import Vehiculo
from app.models.taller import Taller
from app.models.bitacora import Bitacora
from app.models.categoria import Categoria
from app.models.incidente import Incidente, EstadoIncidente
from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.models.servicio_realizado import ServicioRealizado
from app.models.pago import Pago, EstadoPago, MetodoPago
from app.models.comision import Comision
from app.models.calificacion import Calificacion
from app.models.evidencia import Evidencia
from app.models.historial_estado import HistorialEstado
# from app.models.procesamiento_ia import ProcesamientoIA, EstadoProcesamiento