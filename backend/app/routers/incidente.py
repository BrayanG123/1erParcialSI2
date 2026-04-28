from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.incidente import IncidenteCreate, IncidenteRead, IncidenteUpdate
from app.models.incidente import Incidente as IncidenteModel
from app.models.asignacion_servicio import AsignacionServicio
from app.models.usuario import Mecanico
from app.crud.incidente import (
    crear_incidente,
    get_incidentes_de_cliente,
    get_incidentes_disponibles,
    actualizar_incidente,
)
from app.core.dependencies import (
    get_current_cliente,
    get_current_administrador,
)
from app.services.bitacora import BitacoraService


router = APIRouter(prefix="/incidentes", tags=["Incidentes"])


# CLIENTE — reportar un incidente
@router.post("/", response_model=IncidenteRead, status_code=status.HTTP_201_CREATED)
def reportar_incidente(
    datos: IncidenteCreate,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    cliente = usuario.perfil_cliente
    incidente = crear_incidente(db, cliente.id, datos)
    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="REPORTAR_INCIDENTE",
        descripcion=f"Incidente #{incidente.id} reportado",
    )
    return incidente


# CLIENTE — mis incidentes
@router.get("/mis-incidentes", response_model=list[IncidenteRead])
def mis_incidentes(
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    cliente = usuario.perfil_cliente
    return get_incidentes_de_cliente(db, cliente.id)


# ADMIN — ver incidentes disponibles (tablero tipo Uber)
@router.get("/disponibles", response_model=list[IncidenteRead])
def incidentes_disponibles(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    return get_incidentes_disponibles(db)


# ADMIN — listar incidentes de SU taller
@router.get("/", response_model=list[IncidenteRead])
def listar_todos_los_incidentes(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    return (
        db.query(IncidenteModel)
        .join(IncidenteModel.asignacion)
        .join(AsignacionServicio.mecanico)
        .filter(Mecanico.taller_id == taller_id)
        .order_by(IncidenteModel.fecha_hora.desc())
        .all()
    )


# ADMIN — actualizar un incidente (resumen IA, categoría)
@router.patch("/{incidente_id}", response_model=IncidenteRead)
def actualizar_un_incidente(
    incidente_id: int,
    datos: IncidenteUpdate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    incidente = (
        db.query(IncidenteModel)
        .join(IncidenteModel.asignacion)
        .join(AsignacionServicio.mecanico)
        .filter(
            IncidenteModel.id == incidente_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado o no pertenece a tu taller")
    return actualizar_incidente(db, incidente, datos)


# COMPARTIDO — obtener un incidente por ID
@router.get("/{incidente_id}", response_model=IncidenteRead)
def obtener_incidente(
    incidente_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    incidente = (
        db.query(IncidenteModel)
        .join(IncidenteModel.asignacion)
        .join(AsignacionServicio.mecanico)
        .filter(
            IncidenteModel.id == incidente_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado o no pertenece a tu taller")
    return incidente