import logging

from fastapi import FastAPI

from app.config import settings

logging.getLogger("app").setLevel(logging.INFO)
from app.routers import export, pdf, schedules

app = FastAPI(
    title=settings.app_name,
    description="API para extraer oferta de PDF, generar horarios y exportar a PDF/Calendario.",
)

app.include_router(pdf.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(export.router, prefix="/api")


@app.get("/")
def read_root() -> dict:
    return {"message": "Backend operativo", "docs": "/docs"}