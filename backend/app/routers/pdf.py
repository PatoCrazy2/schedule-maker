"""Endpoints para subida y extracción de PDF."""
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import settings
from app.models.schemas import MapaCurricularExtraido, OfertaExtraida
from app.services.ocr_pdf import ocr_disponible
from app.services.pdf_extractor import PdfExtractorService
from app.services.parser_mapa import ParserMapaCurricular

router = APIRouter(prefix="/pdf", tags=["PDF"])
extractor = PdfExtractorService()
parser_mapa = ParserMapaCurricular()


def _ensure_upload_dir() -> Path:
    d = Path(settings.upload_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _data_dir() -> Path:
    """Directorio de PDF de prueba (montado en Docker como volumen data)."""
    return Path(settings.data_dir)


@router.get("/ocr-disponible")
def get_ocr_disponible() -> dict:
    """
    Indica si el OCR (Tesseract) esta disponible para PDFs que son solo imagen.
    Si es true, POST /api/pdf/upload-mapa intentara extraer texto por OCR cuando el PDF no tenga texto.
    """
    return {"ocr_disponible": ocr_disponible()}


@router.get("/list")
def list_data_pdfs() -> dict:
    """
    Lista los PDF disponibles en el directorio data/ (para uso con Docker).
    """
    data = _data_dir()
    if not data.exists():
        return {"files": [], "data_dir": str(data)}
    files = sorted(
        [f.name for f in data.iterdir() if f.suffix.lower() == ".pdf"],
        key=str.lower,
    )
    return {"files": files, "data_dir": str(data)}


@router.post("/extract-from-data", response_model=OfertaExtraida)
def extract_from_data(
    filename: str = Query(..., description="Nombre del PDF en data/ (ej. Ajustes Banner 2026.pdf)"),
) -> OfertaExtraida:
    """
    Extrae oferta desde un PDF que está en el directorio data/.
    Útil cuando el backend corre en Docker con el volumen data montado.
    """
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo no permitido")
    path = _data_dir() / filename
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado en data/: {filename}",
        )
    if path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    return extractor.extract_from_path(path)


@router.post("/upload", response_model=OfertaExtraida)
async def upload_and_extract(file: UploadFile = File(...)) -> OfertaExtraida:
    """
    Sube un PDF de oferta (ej. Banner BUAP) y extrae filas en formato:

    **NRC, Clave, Materia, Secc, Dias, Hora, Profesor, Salon**

    Respuesta:
    - **filas**: lista de registros, uno por cada combinación dia/hora/salon
      (ej. 50030, CCOS 260, Redes de Computadoras, OO1, L, 10:00-10:59, TREVINO - SANCHEZ DANIEL, 1CCO4/305).
    - **materias**: vista agrupada por materia para horarios y export.
    - **archivos_procesados**: nombre del PDF.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Se requiere un archivo PDF")

    upload_dir = _ensure_upload_dir()
    size_mb = settings.max_upload_mb
    content = await file.read()
    if len(content) > size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {size_mb} MB",
        )

    return extractor.extract_from_bytes(content, file.filename or "document.pdf")


@router.post("/upload-mapa", response_model=MapaCurricularExtraido)
async def upload_mapa_curricular(
    file: UploadFile | None = File(None, description="PDF del mapa curricular. Enviar como multipart/form-data con la clave 'file'."),
) -> MapaCurricularExtraido:
    """
    Sube un PDF de mapa curricular (malla curricular) y extrae las materias del plan.

    **Importante:** La petición debe ser **multipart/form-data** con un campo llamado **file**
    (no JSON). En Swagger: elegir archivo en el input 'file' y luego Execute.

    En cada bloque del mapa se espera: nombre de la materia y cuatro números
    (Horas teoría, Horas lab, Trabajo indep., Créditos). Si el PDF es solo imagen,
    la extracción puede quedar vacía (en el futuro se podría usar OCR).
    """
    if file is None or not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Falta el archivo. Envie el PDF como multipart/form-data con el campo 'file' (no JSON).",
        )
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Se requiere un archivo PDF")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Límite {settings.max_upload_mb} MB")
    return parser_mapa.parsear_desde_bytes(content, file.filename or "mapa.pdf")
