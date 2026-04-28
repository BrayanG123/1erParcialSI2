from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.vehiculo import VehiculoCreate, VehiculoRead, VehiculoUpdate
from app.crud.vehiculo import (
    crear_vehiculo,
    get_vehiculo,
    get_vehiculos_by_cliente,
    actualizar_vehiculo,
    eliminar_vehiculo
)
from app.core.dependencies import get_current_cliente, get_current_superadmin
from app.crud.vehiculo import (
    crear_vehiculo,
    get_vehiculo,
    get_vehiculos_by_cliente,
    get_all_vehiculos,
    actualizar_vehiculo,
    eliminar_vehiculo
)

router = APIRouter(prefix="/vehiculos", tags=["Vehiculos"])

@router.get("/", response_model=List[VehiculoRead])
def listar_todos_vehiculos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_superadmin)
):
    """Lista todos los vehículos registrados en el sistema (Solo Superadmin)."""
    return get_all_vehiculos(db)

@router.post("/", response_model=VehiculoRead, status_code=status.HTTP_201_CREATED)
def post_vehiculo(
    datos: VehiculoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_cliente)
):
    """Permite al cliente registrar un vehículo."""
    return crear_vehiculo(db, datos, usuario.perfil_cliente.id)

@router.get("/mis-vehiculos", response_model=List[VehiculoRead])
def listar_mis_vehiculos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_cliente)
):
    """Lista los vehículos del cliente autenticado."""
    return get_vehiculos_by_cliente(db, usuario.perfil_cliente.id)

@router.get("/{vehiculo_id}", response_model=VehiculoRead)
def obtener_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_cliente)
):
    """Obtiene detalles de un vehículo específico del cliente."""
    vehiculo = get_vehiculo(db, vehiculo_id)
    if not vehiculo or vehiculo.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return vehiculo

@router.patch("/{vehiculo_id}", response_model=VehiculoRead)
def patch_vehiculo(
    vehiculo_id: int,
    datos: VehiculoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_cliente)
):
    """Actualiza los datos de un vehículo."""
    vehiculo = get_vehiculo(db, vehiculo_id)
    if not vehiculo or vehiculo.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return actualizar_vehiculo(db, vehiculo, datos)

@router.delete("/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_cliente)
):
    """Elimina un vehículo."""
    vehiculo = get_vehiculo(db, vehiculo_id)
    if not vehiculo or vehiculo.cliente_id != usuario.perfil_cliente.id:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    eliminar_vehiculo(db, vehiculo)
    return None
