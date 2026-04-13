from fastapi import FastAPI
from app.config import settings
from app.models import Base

#temporales
# from sqlalchemy.orm import Session 
# from sqlalchemy import text
# from app.config import settings
# from app.database import get_db

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de auxilio vehicular tipo Uber",
    docs_url="/docs",
    redoc_url="/redoc" if settings.DEBUG else None
)


@app.get("/")
def root():
    return {"mennsage": f"{settings.APP_NAME} funcionando"}


@app.get("/salud")
def health_check():
    return {"estado": "ok"}

# temporal
# @app.get("/db-test")
# def test_db(db: Session = Depends(get_db)):
#     try:
#         db.execute(text("SELECT 1"))
#         return {"base_de_datos": "conectada correctamente"}
#     except Exception as e:
#         return {"error": str(e)}