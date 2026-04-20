from sqlalchemy.orm import Session

from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


def crear_categoria(db: Session, datos: CategoriaCreate) -> Categoria:
    categoria = Categoria(**datos.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def get_categoria_por_id(db: Session, categoria_id: int) -> Categoria | None:
    return db.query(Categoria).filter(Categoria.id == categoria_id).first()


def get_categoria_por_nombre(db: Session, nombre: str) -> Categoria | None:
    return db.query(Categoria).filter(Categoria.nombre == nombre).first()


def get_todas_las_categorias(db: Session) -> list[Categoria]:
    return db.query(Categoria).order_by(Categoria.prioridad.desc(), Categoria.nombre).all()


def actualizar_categoria(db: Session, categoria: Categoria, datos: CategoriaUpdate) -> Categoria:
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    return categoria


def eliminar_categoria(db: Session, categoria: Categoria) -> None:
    db.delete(categoria)
    db.commit()