from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, RolUsuario, Mecanico
from app.models.pago import EstadoPago, Pago as PagoModel
from app.models.asignacion_servicio import AsignacionServicio
from app.models.servicio_realizado import ServicioRealizado
from app.schemas.pago import PagoCreate, PagoMarcarPagado, PagoRead
from app.crud.pago import crear_pago, get_pago_por_servicio, get_pago_por_id, marcar_pagado
from app.crud.comision import crear_comision, get_comision_por_servicio
from app.crud.servicio_realizado import get_servicio_por_id
from app.core.dependencies import get_cliente_o_admin, get_current_administrador, get_current_usuario
from app.services.bitacora import BitacoraService

router = APIRouter(prefix="/pagos", tags=["Pagos"])

@router.post("/", response_model=PagoRead, status_code=status.HTTP_201_CREATED)
def registrar_pago(
    datos: PagoCreate,
    usuario: Usuario = Depends(get_cliente_o_admin),
    db: Session = Depends(get_db),
):
    servicio = get_servicio_por_id(db, datos.servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    incidente = servicio.asignacion.incidente

    # Cliente: solo puede pagar sus propios servicios
    if usuario.rol.value == "cliente":
        if incidente.cliente.usuario_id != usuario.id:
            raise HTTPException(status_code=403, detail="Este servicio no es tuyo")

    # Admin: solo puede registrar pagos de servicios de SU taller
    if usuario.rol.value == "administrador":
        taller_id = usuario.perfil_administrador.taller_id
        servicio_del_taller = (
            db.query(ServicioRealizado)
            .join(ServicioRealizado.asignacion)
            .join(AsignacionServicio.mecanico)
            .filter(
                ServicioRealizado.id == datos.servicio_id,
                Mecanico.taller_id == taller_id
            )
            .first()
        )
        if not servicio_del_taller:
            raise HTTPException(status_code=403, detail="Este servicio no pertenece a tu taller")

    existente = get_pago_por_servicio(db, datos.servicio_id)
    if existente:
        raise HTTPException(status_code=400, detail="Este servicio ya tiene un pago registrado")

    pago = crear_pago(db, datos)
    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="REGISTRAR_PAGO",
        descripcion=f"Pago #{pago.id} registrado para servicio #{datos.servicio_id}",
    )
    return pago

@router.patch("/{pago_id}/pagar", response_model=PagoRead)
def marcar_como_pagado(
    pago_id: int,
    datos: PagoMarcarPagado,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    pago = get_pago_por_id(db, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    # Verificar que el pago pertenece al taller del admin
    servicio_del_taller = (
        db.query(ServicioRealizado)
        .join(ServicioRealizado.asignacion)
        .join(AsignacionServicio.mecanico)
        .filter(
            ServicioRealizado.id == pago.servicio_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not servicio_del_taller:
        raise HTTPException(status_code=403, detail="Este pago no pertenece a tu taller")

    if pago.estado != EstadoPago.pendiente:
        raise HTTPException(status_code=400, detail="Este pago ya fue procesado")

    pago = marcar_pagado(db, pago, datos)

    existente_comision = get_comision_por_servicio(db, pago.servicio_id)
    if not existente_comision:
        crear_comision(db, pago.servicio_id)

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="CONFIRMAR_PAGO",
        descripcion=f"Pago #{pago_id} marcado como 'pagado'",
    )
    return pago


# ── CLIENTE / ADMIN — ver pago de un servicio ──────────────────────────────────────────
@router.get("/servicio/{servicio_id}", response_model=PagoRead)
def pago_de_servicio(
    servicio_id: int,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """Admin: ve cualquier pago. Cliente: solo ve el pago de sus servicios."""

    if usuario.rol == RolUsuario.administrador:
        taller_id = usuario.perfil_administrador.taller_id

        servicio_del_taller = (
            db.query(ServicioRealizado)
            .join(ServicioRealizado.asignacion)
            .join(AsignacionServicio.mecanico)
            .filter(
                ServicioRealizado.id == servicio_id,
                Mecanico.taller_id == taller_id
            )
            .first()
        )
        if not servicio_del_taller:
            raise HTTPException(status_code=403, detail="Este servicio no pertenece a tu taller")

    
    
    pago = get_pago_por_servicio(db, servicio_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Aún no hay pago para este servicio")
    
    if usuario.rol == RolUsuario.cliente:
        servicio = get_servicio_por_id(db, servicio_id)
        if not servicio:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        incidente = servicio.asignacion.incidente
        if incidente.cliente.usuario_id != usuario.id:
            raise HTTPException(status_code=403, detail="No autorizado")
        
    return pago

@router.get("/", response_model=list[PagoRead])
def listar_pagos(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    return (
        db.query(PagoModel)
        .join(PagoModel.servicio)
        .join(ServicioRealizado.asignacion)
        .join(AsignacionServicio.mecanico)
        .filter(Mecanico.taller_id == taller_id)
        .order_by(PagoModel.fecha_pago.desc())
        .all()
    )