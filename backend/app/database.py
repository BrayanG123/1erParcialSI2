from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings
from app.models.base import Base


# 1. Crear el engine con la URL de la base de datos
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG
)


# 2. Fábrica de sesiones — no crea la sesión todavía, solo la configura
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# 3. Clase base para todos los modelos
# class Base(DeclarativeBase):
#     pass


# 4. Dependencia para inyectar la sesión en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()