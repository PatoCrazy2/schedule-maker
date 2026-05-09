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
    # Warm-up: inicializar Tesseract en background para que la primera
    # llamada a /upload-kardex no pague el costo de inicializacion (~0.5s)
    try:
        from app.services.kardex_ocr_parser import _ocr_disponible
        import asyncio
        loop = asyncio.get_event_loop()
        disponible = await loop.run_in_executor(None, _ocr_disponible)
        if disponible:
            print("Tesseract OCR listo para kardex.")
        else:
            print("Tesseract no disponible — kardex usara solo ruta vectorial.")
    except Exception as e:
        print(f"Warm-up OCR omitido: {e}")
    yield


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.app_name,
    description="API para extraer oferta de PDF, generar horarios y exportar a PDF/Calendario.",
    lifespan=lifespan,
)

# Configurar CORS para permitir peticiones desde el frontend (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://scheduleemaker.vercel.app"],  # En producción, restringe esto a la URL de tu frontend en Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdf.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(professors.router, prefix="/api")
app.include_router(queries.router, prefix="/api")


@app.get("/")
def read_root() -> dict:
    return {"message": "Backend operativo", "docs": "/docs"}
