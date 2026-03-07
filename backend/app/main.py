import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.config import settings
from app.routers import export, pdf, professors, schedules, queries
from app.core.database import init_db

logging.getLogger("app").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando DB y creando tablas si no existen...")
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="API para extraer oferta de PDF, generar horarios y exportar a PDF/Calendario.",
    lifespan=lifespan,
)

app.include_router(pdf.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(professors.router, prefix="/api")
app.include_router(queries.router, prefix="/api")


@app.get("/")
def read_root() -> dict:
    return {"message": "Backend operativo", "docs": "/docs"}
