"""
stripe_pago.py — Pagos con tarjeta vía Stripe Checkout.

Flujo:
  1. Cliente (móvil) → POST /pagos/stripe/checkout {servicio_id}
     - Se crea (o reutiliza) el Pago en estado 'pendiente' con método 'pasarela'.
     - Se crea una Stripe Checkout Session; su id se guarda en pago.referencia.
     - Se devuelve checkout_url → el móvil la abre en el navegador externo.
  2. El cliente paga en la página de Stripe.
  3. Confirmación (dos caminos, ambos idempotentes):
     a) Webhook POST /pagos/stripe/webhook (producción; requiere URL pública
        o `stripe listen --forward-to localhost:8000/pagos/stripe/webhook`).
     b) POST /pagos/stripe/confirmar/{pago_id}: el móvil lo llama al volver
        del navegador; el backend consulta la sesión directamente a Stripe.
        Esto hace que el flujo funcione en desarrollo SIN webhook.
  4. Al confirmar: pago → 'pagado', se genera la comisión y se notifica al
     cliente por push (igual que el flujo manual del admin).
"""
import logging
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_cliente
from app.crud.comision import crear_comision, get_comision_por_servicio
from app.crud.pago import get_pago_por_id, get_pago_por_servicio
from app.crud.servicio_realizado import get_servicio_por_id
from app.database import get_db
from app.models.pago import EstadoPago, MetodoPago, Pago
from app.models.usuario import Usuario
from app.schemas.pago import PagoRead
from app.services.notificacion_service import notificar_cliente_cambio_estado

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/pagos/stripe", tags=["Pagos Stripe"])


class StripeCheckoutRequest(BaseModel):
    servicio_id: int


class StripeCheckoutResponse(BaseModel):
    pago_id: int
    session_id: str
    checkout_url: str


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _servicio_del_cliente(db: Session, servicio_id: int, usuario: Usuario):
    """Valida que el servicio exista y pertenezca al cliente autenticado."""
    servicio = get_servicio_por_id(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    incidente = servicio.asignacion.incidente
    if incidente.cliente.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Este servicio no es tuyo")
    return servicio


def _confirmar_pago(db: Session, pago: Pago, referencia: str | None) -> None:
    """
    Marca el pago como pagado, genera la comisión y notifica al cliente.
    Idempotente: si ya está pagado no hace nada (webhook y confirmar
    pueden llegar ambos).
    """
    if pago.estado == EstadoPago.pagado:
        return

    pago.estado = EstadoPago.pagado
    pago.metodo = MetodoPago.pasarela
    pago.fecha_pago = datetime.utcnow()
    if referencia:
        pago.referencia = referencia
    db.commit()
    db.refresh(pago)

    # Comisión de la plataforma (igual que cuando el admin confirma efectivo)
    if not get_comision_por_servicio(db, pago.servicio_id):
        try:
            crear_comision(db, pago.servicio_id)
        except Exception as e:
            logger.error(f"Error creando comisión del pago #{pago.id}: {e}")

    # Notificar al cliente por push
    try:
        servicio = get_servicio_por_id(db, pago.servicio_id)
        incidente = servicio.asignacion.incidente
        notificar_cliente_cambio_estado(
            db=db,
            cliente_usuario_id=incidente.cliente.usuario_id,
            incidente_id=incidente.id,
            mensaje=f"Tu pago de Bs. {pago.monto:.2f} fue confirmado. ¡Gracias!",
            tipo="pago_confirmado",
        )
    except Exception as e:
        logger.error(f"Error notificando pago #{pago.id}: {e}")


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@router.post("/checkout", response_model=StripeCheckoutResponse)
def crear_checkout(
    datos: StripeCheckoutRequest,
    request: Request,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """Crea la sesión de Stripe Checkout para pagar un servicio realizado."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe no está configurado en el servidor")

    servicio = _servicio_del_cliente(db, datos.servicio_id, usuario)

    # Reutilizar el pago pendiente si existe; crearlo si no
    pago = get_pago_por_servicio(db, datos.servicio_id)
    if pago and pago.estado == EstadoPago.pagado:
        raise HTTPException(status_code=400, detail="Este servicio ya fue pagado")
    if not pago:
        pago = Pago(
            servicio_id=servicio.id,
            monto=servicio.costo_final,
            metodo=MetodoPago.pasarela,
            estado=EstadoPago.pendiente,
        )
        db.add(pago)
        db.flush()

    # Páginas de retorno servidas por este mismo backend (el móvil
    # detecta el pago vía /confirmar, estas páginas son informativas)
    base = str(request.base_url).rstrip("/")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "bob",
                "product_data": {
                    "name": f"Servicio #{servicio.id} — {servicio.tipo_servicio}",
                },
                "unit_amount": int(round(servicio.costo_final * 100)),
            },
            "quantity": 1,
        }],
        metadata={
            "pago_id": str(pago.id),
            "servicio_id": str(servicio.id),
        },
        success_url=f"{base}/pagos/stripe/exito",
        cancel_url=f"{base}/pagos/stripe/cancelado",
    )

    # Guardamos el id de la sesión para poder verificarla después
    pago.metodo = MetodoPago.pasarela
    pago.referencia = session.id
    db.commit()
    db.refresh(pago)

    return StripeCheckoutResponse(
        pago_id=pago.id,
        session_id=session.id,
        checkout_url=session.url,
    )


@router.post("/confirmar/{pago_id}", response_model=PagoRead)
def confirmar_pago_stripe(
    pago_id: int,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    """
    Verificación activa: consulta la Checkout Session directamente a Stripe.
    El móvil hace polling de este endpoint al volver del navegador.
    Devuelve el pago con su estado actual (pagado o aún pendiente).
    """
    pago = get_pago_por_id(db, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    _servicio_del_cliente(db, pago.servicio_id, usuario)  # valida propiedad

    if pago.estado == EstadoPago.pagado:
        return pago

    if not pago.referencia or not pago.referencia.startswith("cs_"):
        raise HTTPException(status_code=400, detail="Este pago no tiene una sesión de Stripe asociada")

    session = stripe.checkout.Session.retrieve(pago.referencia)
    if session.payment_status == "paid":
        _confirmar_pago(db, pago, referencia=session.payment_intent or session.id)

    return pago


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook de Stripe (producción). En desarrollo:
        stripe listen --forward-to localhost:8000/pagos/stripe/webhook
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Firma de webhook inválida")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        pago_id = session.get("metadata", {}).get("pago_id")
        if pago_id:
            pago = get_pago_por_id(db, int(pago_id))
            if pago:
                _confirmar_pago(
                    db, pago,
                    referencia=session.get("payment_intent") or session.get("id"),
                )
                logger.info(f"Webhook: pago #{pago_id} confirmado")

    return {"status": "ok"}


# Páginas simples de retorno (se abren en el navegador del cliente)
_HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;
min-height:90vh;background:#f8fafc}}div{{text-align:center;padding:40px;background:#fff;
border-radius:24px;box-shadow:0 4px 24px rgba(0,0,0,.06)}}h1{{font-size:48px;margin:0}}
p{{color:#64748b}}</style></head><body><div><h1>{icono}</h1><h2>{titulo}</h2>
<p>{mensaje}</p></div></body></html>"""


@router.get("/exito", response_class=HTMLResponse, include_in_schema=False)
def pagina_exito():
    return _HTML.format(
        icono="✅", titulo="¡Pago exitoso!",
        mensaje="Ya puedes cerrar esta ventana y volver a la app.",
    )


@router.get("/cancelado", response_class=HTMLResponse, include_in_schema=False)
def pagina_cancelado():
    return _HTML.format(
        icono="✖️", titulo="Pago cancelado",
        mensaje="No se realizó ningún cobro. Puedes volver a la app e intentarlo de nuevo.",
    )
