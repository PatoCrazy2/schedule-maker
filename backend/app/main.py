import logging
from contextlib import asynccontextmanager # <--- 1. Importar esto
from fastapi import FastAPI
from app.config import settings
from app.routers import export, pdf, schedules
from app.core.database import init_db  

# Configuración de Logs
logging.getLogger("app").setLevel(logging.INFO)

# 3. Definir el Lifespan (Lo que pasa al arrancar)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Aquí llamamos a la creación de tablas
    print("🚀 Iniciando DB y creando tablas si no existen...")
    init_db()
    yield
    # Aquí iría código para cuando se apaga la app (opcional)

# 4. Inyectar el lifespan en FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API para extraer oferta de PDF, generar horarios y exportar a PDF/Calendario.",
    lifespan=lifespan # <--- CONECTARLO AQUÍ
)

app.include_router(pdf.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(export.router, prefix="/api")

@app.get("/")
def read_root() -> dict:
    return {"message": "Backend operativo", "docs": "/docs"}