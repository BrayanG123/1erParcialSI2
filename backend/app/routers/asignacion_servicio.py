from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.asignacion_servicio import AsignacionServicio, EstadoAsignacion
from app.models.usuario import Mecanico
from app.schemas.asignacion_servicio import (
    AsignacionCreate,
    AsignacionRead,
    AsignacionRechazar,
    AsignacionEstadoUpdate,
    AsignacionAsignarMecanico,
)
from app.crud.asignacion_servicio import (
    crear_asignacion,
    get_asignacion_por_id,
    get_asignacion_por_incidente,
    get_asignaciones_de_mecanico,
    aceptar_asignacion,
    rechazar_asignacion,
    actualizar_estado_asignacion,
)
from app.crud.incidente import get_incidente_por_id, marcar_no_disponible
from app.core.dependencies import (
    get_current_administrador,
    get_current_mecanico,
    get_current_usuario,
)
from app.services.bitacora import BitacoraService
from app.models.incidente import EstadoIncidente
from app.services.websocket_manager import manager
from app.services.notificacion_service import notificar_cliente_cambio_estado



router = APIRouter(prefix="/asignaciones", tags=["Asignaciones de Servicio"])


# ADMIN — crear una asignación
@router.post("/", response_model=AsignacionRead, status_code=status.HTTP_201_CREATED)
def crear_nueva_asignacion(
    datos: AsignacionCreate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    existente = get_asignacion_por_incidente(db, datos.incidente_id)
    if existente and existente.estado not in (
        EstadoAsignacion.rechazada,
        EstadoAsignacion.cancelado,
    ):
        raise HTTPException(
            status_code=400,
            detail="El incidente ya tiene una asignación activa"
        )

    incidente = get_incidente_por_id(db, datos.incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    if incidente.estado != EstadoIncidente.disponible:
        raise HTTPException(status_code=400, detail="El incidente no está disponible")

    admin_perfil = usuario.perfil_administrador
    taller_id = admin_perfil.taller_id

    # Verificar mecánico solo si se proporcionó uno
    if datos.mecanico_id is not None:
        mecanico = db.query(Mecanico).filter(
            Mecanico.id == datos.mecanico_id,
            Mecanico.taller_id == taller_id
        ).first()
        if not mecanico:
            raise HTTPException(
                status_code=403,
                detail="El mecánico no pertenece a tu taller"
            )

    asignacion = crear_asignacion(db, datos)

    # Vincular la asignación al tenant del admin para que sea visible en el listado
    if admin_perfil.tenant_id and asignacion.tenant_id is None:
        asignacion.tenant_id = admin_perfil.tenant_id
        db.commit()
        db.refresh(asignacion)

    marcar_no_disponible(db, incidente)

    # ── Notificar al cliente: su incidente fue aceptado por un taller ────
    # (este es el flujo que usa el botón "Aceptar" de Solicitudes disponibles)
    try:
        if incidente.cliente:
            notificar_cliente_cambio_estado(
                db=db,
                cliente_usuario_id=incidente.cliente.usuario_id,
                incidente_id=incidente.id,
                mensaje="¡Tu incidente fue aceptado por un taller! Pronto te asignarán un mecánico.",
                tipo="estado_asignacion",
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error enviando push al cliente: {e}")
    # ─────────────────────────────────────────────────────────────────────

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="CREAR_ASIGNACION",
        descripcion=f"Asignación #{asignacion.id} creada para incidente #{datos.incidente_id}",
        entidad_afectada="asignacion",
    )
    return asignacion


# ADMIN — listar asignaciones de SU taller
@router.get("/", response_model=list[AsignacionRead])
def listar_asignaciones(
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    admin_perfil = usuario.perfil_administrador
    taller_id = admin_perfil.taller_id
    tenant_id = admin_perfil.tenant_id

    q = db.query(AsignacionServicio).outerjoin(AsignacionServicio.mecanico)

    if tenant_id:
        # Incluye asignaciones vinculadas al tenant (pueden no tener mecánico aún)
        # y también las antiguas donde el mecánico es de este taller
        q = q.filter(
            or_(
                AsignacionServicio.tenant_id == tenant_id,
                Mecanico.taller_id == taller_id,
            )
        )
    else:
        q = q.filter(Mecanico.taller_id == taller_id)

    return q.order_by(AsignacionServicio.fecha_creacion.desc()).all()


# ADMIN — asignar (o reasignar) un mecánico a una asignación aceptada
@router.patch("/{asignacion_id}/asignar-mecanico", response_model=AsignacionRead)
def asignar_mecanico_a_asignacion(
    asignacion_id: int,
    datos: AsignacionAsignarMecanico,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    Asigna un mecánico del taller a una asignación existente.
    Si la asignación estaba 'pendiente' pasa a 'taller_asignado'
    y se notifica al cliente por push.
    """
    admin_perfil = usuario.perfil_administrador
    taller_id = admin_perfil.taller_id
    tenant_id = admin_perfil.tenant_id

    q = (
        db.query(AsignacionServicio)
        .outerjoin(AsignacionServicio.mecanico)
        .filter(AsignacionServicio.id == asignacion_id)
    )
    if tenant_id:
        q = q.filter(
            or_(
                AsignacionServicio.tenant_id == tenant_id,
                Mecanico.taller_id == taller_id,
            )
        )
    else:
        q = q.filter(Mecanico.taller_id == taller_id)

    asignacion = q.first()
    if not asignacion:
        raise HTTPException(
            status_code=404,
            detail="Asignación no encontrada o no pertenece a tu taller"
        )

    if asignacion.estado not in (EstadoAsignacion.pendiente, EstadoAsignacion.taller_asignado):
        raise HTTPException(
            status_code=400,
            detail=f"No puedes asignar mecánico a una asignación en estado '{asignacion.estado.value}'"
        )

    mecanico = db.query(Mecanico).filter(
        Mecanico.id == datos.mecanico_id,
        Mecanico.taller_id == taller_id
    ).first()
    if not mecanico:
        raise HTTPException(
            status_code=403,
            detail="El mecánico no pertenece a tu taller"
        )

    asignacion.mecanico_id = mecanico.id
    if asignacion.estado == EstadoAsignacion.pendiente:
        asignacion.estado = EstadoAsignacion.taller_asignado
    if asignacion.fecha_respuesta is None:
        asignacion.fecha_respuesta = datetime.utcnow()
    db.commit()
    db.refresh(asignacion)

    # ── Notificar al cliente: mecánico asignado ──────────────────────────
    try:
        incidente = get_incidente_por_id(db, asignacion.incidente_id)
        if incidente and incidente.cliente:
            nombre_mecanico = (
                f"{mecanico.usuario.nombre} {mecanico.usuario.apellido}"
                if mecanico.usuario else "un mecánico"
            )
            notificar_cliente_cambio_estado(
                db=db,
                cliente_usuario_id=incidente.cliente.usuario_id,
                incidente_id=incidente.id,
                mensaje=f"Se te asignó el mecánico {nombre_mecanico}. Pronto estará en camino.",
                tipo="estado_asignacion",
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error enviando push al cliente: {e}")
    # ─────────────────────────────────────────────────────────────────────

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="ASIGNAR_MECANICO",
        descripcion=f"Mecánico #{mecanico.id} asignado a asignación #{asignacion_id}",
        entidad_afectada="asignacion",
    )

    return asignacion


# MECÁNICO — ver mis asignaciones
@router.get("/mis-asignaciones", response_model=list[AsignacionRead])
def mis_asignaciones(
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    mecanico = usuario.perfil_mecanico
    return get_asignaciones_de_mecanico(db, mecanico.id)


# ADMIN — rechazar una asignación de su taller
@router.patch("/{asignacion_id}/rechazar", response_model=AsignacionRead)
def rechazar_mi_asignacion(
    asignacion_id: int,
    datos: AsignacionRechazar,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    taller_id = usuario.perfil_administrador.taller_id

    asignacion = (
        db.query(AsignacionServicio)
        .join(AsignacionServicio.mecanico)
        .filter(
            AsignacionServicio.id == asignacion_id,
            Mecanico.taller_id == taller_id
        )
        .first()
    )
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada o no pertenece a tu taller")

    if asignacion.estado != EstadoAsignacion.pendiente:
        raise HTTPException(
            status_code=400,
            detail=f"No puedes rechazar una asignación en estado '{asignacion.estado.value}'"
        )

    resultado = rechazar_asignacion(db, asignacion, datos.motivo_rechazo)

    # ── Notificar al cliente: taller rechazó ─────────────────────────────
    try:
        incidente = get_incidente_por_id(db, asignacion.incidente_id)
        if incidente and incidente.cliente:
            notificar_cliente_cambio_estado(
                db=db,
                cliente_usuario_id=incidente.cliente.usuario_id,
                incidente_id=incidente.id,
                mensaje="El taller rechazó tu incidente. Buscaremos otro.",
                tipo="estado_asignacion",
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error enviando push al cliente: {e}")
    # ─────────────────────────────────────────────────────────────────────

    return resultado


# ADMIN — aceptar una asignación (pasar de pendiente → taller_asignado)
@router.patch("/{asignacion_id}/aceptar", response_model=AsignacionRead)
def aceptar_mi_asignacion(
    asignacion_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    """
    El administrador acepta una asignación pendiente.
    Cambia el estado de 'pendiente' a 'taller_asignado'.
    A partir de aquí el mecánico puede avanzar su estado.
    """
    taller_id = usuario.perfil_administrador.taller_id

    asignacion = (
        db.query(AsignacionServicio)
        .join(AsignacionServicio.mecanico)
        .filter(
            AsignacionServicio.id == asignacion_id,
            Mecanico.taller_id == taller_id,
        )
        .first()
    )
    if not asignacion:
        raise HTTPException(
            status_code=404,
            detail="Asignación no encontrada o no pertenece a tu taller"
        )

    if asignacion.estado != EstadoAsignacion.pendiente:
        raise HTTPException(
            status_code=400,
            detail=f"Solo puedes aceptar asignaciones en estado 'pendiente'. "
                   f"Estado actual: '{asignacion.estado.value}'"
        )

    resultado = aceptar_asignacion(db, asignacion)

    # ── Notificar al cliente: taller aceptó ──────────────────────────────
    try:
        incidente = get_incidente_por_id(db, asignacion.incidente_id)
        if incidente and incidente.cliente:
            notificar_cliente_cambio_estado(
                db=db,
                cliente_usuario_id=incidente.cliente.usuario_id,
                incidente_id=incidente.id,
                mensaje="¡Tu incidente fue aceptado por un taller!",
                tipo="estado_asignacion",
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error enviando push al cliente: {e}")
    # ─────────────────────────────────────────────────────────────────────

    BitacoraService.registrar(
        db=db,
        usuario_id=usuario.id,
        accion="ACEPTAR_ASIGNACION",
        descripcion=f"Asignación #{asignacion_id} aceptada por admin taller #{taller_id}",
        entidad_afectada="asignacion",
    )

    return resultado


# MECÁNICO — avanzar estado de su asignación
@router.patch("/{asignacion_id}/estado", response_model=AsignacionRead)
async def cambiar_estado_asignacion(
    asignacion_id: int,
    datos: AsignacionEstadoUpdate,
    usuario: Usuario = Depends(get_current_mecanico),
    db: Session = Depends(get_db),
):
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    mecanico = usuario.perfil_mecanico
    if asignacion.mecanico_id != mecanico.id:
        raise HTTPException(status_code=403, detail="Esta asignación no es tuya")

    transiciones_validas = {
        EstadoAsignacion.taller_asignado: [EstadoAsignacion.en_camino,   EstadoAsignacion.cancelado],
        EstadoAsignacion.en_camino:       [EstadoAsignacion.en_atencion, EstadoAsignacion.cancelado],
        EstadoAsignacion.en_atencion:     [EstadoAsignacion.finalizado],
    }

    estados_permitidos = transiciones_validas.get(asignacion.estado, [])
    if datos.estado not in estados_permitidos:
        permitidos_str = ", ".join(e.value for e in estados_permitidos)
        raise HTTPException(
            status_code=400,
            detail=f"Desde '{asignacion.estado.value}' solo puedes ir a: {permitidos_str}"
        )

    asignacion_actualizada = actualizar_estado_asignacion(db, asignacion, datos)

    # ── Notificar al cliente sobre el cambio de estado ───────────────────
    mensajes_estado = {
        "en_camino":       "El mecánico está en camino a tu ubicación.",
        "en_atencion":     "El mecánico llegó y está atendiendo tu vehículo.",
        "finalizado":      "Tu incidente fue atendido y finalizado.",
        "cancelado":       "Tu incidente fue cancelado.",
    }

    nuevo_estado_str = datos.estado.value  # .value porque EstadoAsignacion es un Enum
    if nuevo_estado_str in mensajes_estado:
        try:
            incidente = get_incidente_por_id(db, asignacion.incidente_id)
            if incidente and incidente.cliente:
                notificar_cliente_cambio_estado(
                    db=db,
                    cliente_usuario_id=incidente.cliente.usuario_id,
                    incidente_id=incidente.id,
                    mensaje=mensajes_estado[nuevo_estado_str],
                    tipo="estado_asignacion",
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error enviando push al cliente: {e}")
    # ─────────────────────────────────────────────────────────────────────


    # --- notificar por WebSocket a todos los conectados al incidente ---
    # Construir datos del mecánico para enviar al cliente
    mecanico_datos = None
    if asignacion.mecanico:
        mecanico_datos = {
            "id": asignacion.mecanico.id,
            "nombre": asignacion.mecanico.usuario.nombre if asignacion.mecanico.usuario else "Mecánico",
            "telefono": asignacion.mecanico.telefono,
            "lat": asignacion.mecanico.latitud,
            "lng": asignacion.mecanico.longitud,
        }

    await manager.broadcast(
        incidente_id=asignacion.incidente_id,
        mensaje={
            "tipo": "cambio_estado",
            "estado": datos.estado.value,
            "asignacion_id": asignacion.id,
            "incidente_id": asignacion.incidente_id,
            "mecanico": mecanico_datos,
        }
    )

    # Limpiar posición del mecánico de memoria si el servicio terminó
    if datos.estado in (EstadoAsignacion.finalizado, EstadoAsignacion.cancelado):
        manager.limpiar_posicion(asignacion.incidente_id)

    return asignacion_actualizada


# COMPARTIDO — obtener una asignación por ID (admin del taller o mecánico dueño)
@router.get("/{asignacion_id}", response_model=AsignacionRead)
def obtener_asignacion(
    asignacion_id: int,
    usuario: Usuario = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    asignacion = get_asignacion_por_id(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    rol = usuario.rol.value

    # Mecánico: solo puede ver SUS asignaciones
    if rol == "mecanico":
        if not usuario.perfil_mecanico or asignacion.mecanico_id != usuario.perfil_mecanico.id:
            raise HTTPException(status_code=403, detail="Esta asignación no es tuya")
        return asignacion

    # Administrador: solo asignaciones de su taller/tenant
    if rol == "administrador":
        admin_perfil = usuario.perfil_administrador
        es_del_tenant = (
            admin_perfil.tenant_id is not None
            and asignacion.tenant_id == admin_perfil.tenant_id
        )
        es_del_taller = (
            asignacion.mecanico is not None
            and asignacion.mecanico.taller_id == admin_perfil.taller_id
        )
        if not (es_del_tenant or es_del_taller):
            raise HTTPException(status_code=403, detail="Esta asignación no pertenece a tu taller")
        return asignacion

    raise HTTPException(status_code=403, detail="No autorizado")