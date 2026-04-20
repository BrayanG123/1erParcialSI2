from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaUpdate
from app.crud.categoria import (
    crear_categoria,
    get_categoria_por_id,
    get_categoria_por_nombre,
    get_todas_las_categorias,
    actualizar_categoria,
    eliminar_categoria,
)
from app.core.dependencies import get_current_administrador, get_current_usuario


router = APIRouter(prefix="/categorias", tags=["Categorias"])



# PÚBLICO — listar todas las categorías
@router.get("/", response_model=list[CategoriaRead])
def listar_categorias(db: Session = Depends(get_db)):
    """Retorna todas las categorías. No requiere autenticación."""
    return get_todas_las_categorias(db)


# PÚBLICO — obtener una categoria por ID
@router.get("/{categoria_id}", response_model=CategoriaRead)
def obtener_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = get_categoria_por_id(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria



# ADMIN — crear categoria
@router.post("/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def crear_nueva_categoria(
    datos: CategoriaCreate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    if get_categoria_por_nombre(db, datos.nombre):
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
    return crear_categoria(db, datos)



# ADMIN — actualizar categoría
@router.patch("/{categoria_id}", response_model=CategoriaRead)
def actualizar_una_categoria(
    categoria_id: int,
    datos: CategoriaUpdate,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    categoria = get_categoria_por_id(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return actualizar_categoria(db, categoria, datos)



# ADMIN — eliminar categoría
@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_una_categoria(
    categoria_id: int,
    usuario: Usuario = Depends(get_current_administrador),
    db: Session = Depends(get_db),
):
    categoria = get_categoria_por_id(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    eliminar_categoria(db, categoria)