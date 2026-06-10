from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import (
    auth,
    usuarios,
    admin,
    superadmin,
    incidente,
    categoria,
    vehiculo,
    taller,
    asignacion_servicio,
    servicio_realizado,
    pago,
    comision,
    calificacion,
    evidencia,
    historial_estado,
    kpi,
    websocket,
    notificaciones,
    web_push
 )


app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de auxilio vehicular tipo Uber",
    docs_url="/docs",
    redoc_url="/redoc" if settings.DEBUG else None
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Registrar routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(admin.router)
app.include_router(superadmin.router)
app.include_router(incidente.router)
app.include_router(categoria.router)
app.include_router(vehiculo.router)
app.include_router(taller.router)
app.include_router(asignacion_servicio.router)
app.include_router(servicio_realizado.router)
app.include_router(pago.router)
app.include_router(comision.router)
app.include_router(calificacion.router)
app.include_router(evidencia.router)
app.include_router(historial_estado.router)
app.include_router(kpi.router)
app.include_router(websocket.router)
app.include_router(notificaciones.router)
app.include_router(web_push.router)


@app.get("/")
def root():
    return {"mennsage": f"{settings.APP_NAME} funcionando"}


@app.get("/salud")
def health_check():
    return {"estado": "ok"}

# @app.get("/db-test")
# def test_db(db: Session = Depends(get_db)):
#     try:
#         db.execute(text("SELECT 1"))
#         return {"base_de_datos": "conectada correctamente"}
#     except Exception as e:
#         return {"error": str(e)}