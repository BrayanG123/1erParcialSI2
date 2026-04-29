from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_current_cliente, get_current_superadmin
from app.crud.vehiculo import (
    crear_vehiculo,
    actualizar_vehiculo,
    eliminar_vehiculo,
    get_vehiculo_por_id,
    get_vehiculos_de_cliente,
    guardar_foto_vehiculo,
)
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.vehiculo import VehiculoCreate, VehiculoRead, VehiculoUpdate

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])

TIPOS_FOTO_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
MAX_FOTO_BYTES = 5 * 1024 * 1024  # 5 MB


# ── Listar mis vehículos ──────────────────────────────────────────────────────
@router.get("", response_model=list[VehiculoRead])
def mis_vehiculos(
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    return get_vehiculos_de_cliente(db, usuario.perfil_cliente.id)


# ── Crear vehículo ────────────────────────────────────────────────────────────
@router.post("", response_model=VehiculoRead, status_code=status.HTTP_201_CREATED)
def crear(
    datos: VehiculoCreate,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    return crear_vehiculo(db, usuario.perfil_cliente.id, datos)


# ── Obtener uno ───────────────────────────────────────────────────────────────
@router.get("/{vehiculo_id}", response_model=VehiculoRead)
def obtener_uno(
    vehiculo_id: int,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    v = get_vehiculo_por_id(db, vehiculo_id)
    if not v or v.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return v


# ── Actualizar datos ──────────────────────────────────────────────────────────
@router.patch("/{vehiculo_id}", response_model=VehiculoRead)
def actualizar(
    vehiculo_id: int,
    datos: VehiculoUpdate,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    v = get_vehiculo_por_id(db, vehiculo_id)
    if not v or v.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return actualizar_vehiculo(db, v, datos)


# ── Subir foto ────────────────────────────────────────────────────────────────
@router.post("/{vehiculo_id}/foto", response_model=VehiculoRead)
def subir_foto(
    vehiculo_id: int,
    foto: UploadFile = File(...),
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    v = get_vehiculo_por_id(db, vehiculo_id)
    if not v or v.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    if foto.content_type not in TIPOS_FOTO_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Usa JPG, PNG o WebP.",
        )
    return guardar_foto_vehiculo(db, v, foto)


# ── Eliminar ──────────────────────────────────────────────────────────────────
@router.delete("/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    vehiculo_id: int,
    usuario: Usuario = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    v = get_vehiculo_por_id(db, vehiculo_id)
    if not v or v.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    eliminar_vehiculo(db, v)