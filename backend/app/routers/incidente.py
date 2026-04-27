from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from app.services.cloudinary_service import subir_imagen
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, RolUsuario
from app.schemas.incidente import IncidenteCreate, IncidenteRead, IncidenteUpdate
from app.models.incidente import EstadoIncidente, Incidente as IncidenteModel
from app.crud.incidente import (
    crear_incidente,
    get_incidente_por_id,
    get_incidentes_de_cliente,
    get_incidentes_disponibles,
    actualizar_incidente,
)
from app.core.dependencies import (
    get_current_cliente,
    get_current_administrador,
    get_current_usuario,
)
from app.services.bitacora import BitacoraService
from app.crud.asignacion_servicio import get_asignacion_por_incidente
from app.schemas.asignacion_servicio import AsignacionRead



router = APIRouter(prefix="/incidentes", tags=["Incidentes"])



# CLIENTE — reportar un incidente
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/", response_model=IncidenteRead, status_code=status.HTTP_201_CREATED)
def reportar_incidente(
    datos: IncidenteCreate,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente reporta un nuevo incidente. Queda en estado 'disponible'."""
    cliente = usuario.perfil_cliente
    incidente = crear_incidente(db, cliente.id, datos)
    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="REPORTAR_INCIDENTE",
        descripcion=f"Incidente #{incidente.id} reportado",
    )
    return incidente



# CLIENTE — mis incidentes ───────────────
@router.get("/mis-incidentes", response_model=list[IncidenteRead])
def mis_incidentes(
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente consulta todos sus incidentes."""
    cliente = usuario.perfil_cliente
    return get_incidentes_de_cliente(db, cliente.id)


# CLIENTE — subir foto a un incidente propio ─────────────────
@router.post("/{incidente_id}/foto", response_model=IncidenteRead)
def subir_foto_incidente(
    incidente_id: int,
    foto: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente sube una foto a su incidente recién creado."""
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente or incidente.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    try:
        url = subir_imagen(foto, carpeta="incidentes")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    incidente.foto_incidente = url
    db.commit()
    db.refresh(incidente)
    return incidente


# CLIENTE — ver la asignación de su propio incidente
@router.get("/{incidente_id}/asignacion", response_model=AsignacionRead)
def obtener_asignacion_de_incidente(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """El cliente consulta si su incidente ya tiene mecánico asignado."""
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente or incidente.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    asignacion = get_asignacion_por_incidente(db, incidente_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Sin asignación aún")

    return asignacion


# CLIENTE — cancelar un incidente propio
# ─────────────────────────────────────────────────────────────────────────────




# ── ADMIN — ver incidentes disponibles (para aceptar) 
@router.get("/disponibles", response_model=list[IncidenteRead])
def incidentes_disponibles(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """El admin del taller ve los incidentes que puede aceptar (como un tablero de Uber)."""
    return get_incidentes_disponibles(db)



# ── ADMIN — listar todos los incidentes ──────────────────────────────────────
@router.get("/", response_model=list[IncidenteRead])
def listar_todos_los_incidentes(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    return db.query(IncidenteModel).order_by(IncidenteModel.fecha_hora.desc()).all()



# ── ADMIN — actualizar un incidente (resumen IA, categoría) ──────────────────
@router.patch("/{incidente_id}", response_model=IncidenteRead)
def actualizar_un_incidente(
    incidente_id: int,
    datos: IncidenteUpdate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    return actualizar_incidente(db, incidente, datos)



# ── COMPARTIDO — obtener un incidente por ID ─────────────────────────────────
@router.get("/{incidente_id}", response_model=IncidenteRead)
def obtener_incidente(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """
    Admin: puede ver cualquier incidente.
    Cliente: solo puede ver sus propios incidentes.
    """
    incidente = get_incidente_por_id(db, incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    
    # Si es cliente, verificar que le pertenece
    if usuario.rol == RolUsuario.cliente:
        if incidente.cliente_id != usuario.perfil_cliente.id:
            raise HTTPException(status_code=403, detail="No autorizado")
        
    return incidente


