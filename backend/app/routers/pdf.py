"""Endpoints para subida y extracción de PDF."""
from pathlib import Path
from datetime import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.config import settings
from app.core.database import get_session
from app.core.redis_client import (
    get_cached_source_file_id,
    set_cached_source_file_id,
)
from app.models.db_models import Course, SourceFile, TimeSlot
from app.models.schemas import (
    DayEnum,
    HorarioSlot,
    MapaCurricularExtraido,
    MateriaExtraida,
    OfertaExtraida,
)
from app.services.ocr_pdf import ocr_disponible
from app.services.pdf_extractor import PdfExtractorService
from app.services.parser_mapa import ParserMapaCurricular
from app.utils.hashing import compute_file_hash

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
    """
    return {"ocr_disponible": ocr_disponible()}


@router.get("/list")
def list_data_pdfs() -> dict:
    """Lista los PDF disponibles en el directorio data/."""
    data = _data_dir()
    if not data.exists():
        return {"files": [], "data_dir": str(data)}
    files = sorted(
        [f.name for f in data.iterdir() if f.suffix.lower() == ".pdf"],
        key=str.lower,
    )
    return {"files": files, "data_dir": str(data)}


@router.get("/file")
def get_pdf_file(
    filename: str = Query(..., description="Nombre del PDF en data/ para visualizar"),
):
    """Sirve un PDF del directorio data/ para visualización."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo no permitido")
    path = _data_dir() / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {filename}")
    if path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@router.post("/extract-from-data", response_model=OfertaExtraida)
def extract_from_data(
    filename: str = Query(..., description="Nombre del PDF en data/ (ej. Ajustes Banner 2026.pdf)"),
) -> OfertaExtraida:
    """Extrae oferta desde un PDF que está en el directorio data/."""
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


def _source_file_to_oferta(source: SourceFile) -> OfertaExtraida:
    """Reconstruye OfertaExtraida desde un SourceFile en BD."""
    materias_recuperadas = []
    for course in source.courses:
        horarios_legacy = [
            HorarioSlot(
                dia=slot.day.value,
                hora_inicio=slot.start_time.strftime("%H:%M"),
                hora_fin=slot.end_time.strftime("%H:%M"),
                aula=slot.classroom,
            )
            for slot in course.time_slots
        ]
        materias_recuperadas.append(
            MateriaExtraida(
                nrc=course.nrc,
                nombre=course.subject_name,
                clave=course.course_code,
                grupo=course.group_code,
                profesor=course.professor,
                creditos=course.credits,
                horarios=horarios_legacy,
            )
        )
    return OfertaExtraida(
        filas=_reconstruir_filas_desde_courses(source),
        materias=materias_recuperadas,
        archivos_procesados=[source.filename],
    )


def _reconstruir_filas_desde_courses(source: SourceFile) -> list:
    """Reconstruye filas desde courses para compatibilidad con frontend."""
    from app.models.schemas import FilaOferta

    filas = []
    for course in source.courses:
        for slot in course.time_slots:
            filas.append(
                FilaOferta(
                    nrc=course.nrc,
                    clave=course.course_code,
                    materia=course.subject_name,
                    secc=course.group_code,
                    dias=slot.day.value,
                    hora_inicio=slot.start_time.strftime("%H:%M"),
                    hora_fin=slot.end_time.strftime("%H:%M"),
                    profesor=course.professor or "",
                    salon=slot.classroom or "",
                )
            )
    return filas


@router.post("/upload", response_model=OfertaExtraida)
async def upload_and_extract(
    file: UploadFile = File(...),
    carrera: str | None = Form(None, description="Carrera o profesión (opcional)"),
    session: Session = Depends(get_session),
) -> OfertaExtraida:
    """
    Sube un PDF de oferta (ej. Banner BUAP) y extrae filas.
    Cache por hash (Redis + BD): mismo documento = reutiliza extracción (varios usuarios).
    carrera: opcional, para organizar PDFs por carrera.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Se requiere un archivo PDF")

    _ensure_upload_dir()
    size_mb = settings.max_upload_mb

    try:
        content = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Error leyendo el archivo")

    if len(content) > size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {size_mb} MB",
        )

    file_hash = compute_file_hash(content)

    # 1. Cache Redis: busqueda rapida por hash
    cached_id = get_cached_source_file_id(file_hash)
    if cached_id is not None:
        try:
            existing_file = session.get(SourceFile, cached_id)
            if existing_file and existing_file.courses:
                return _source_file_to_oferta(existing_file)
        except Exception:
            pass

    # 2. BD: busqueda por hash
    try:
        existing_file = session.exec(
            select(SourceFile).where(SourceFile.file_hash == file_hash)
        ).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

    if existing_file:
        if not existing_file.courses:
            session.delete(existing_file)
            session.commit()
            existing_file = None
        else:
            set_cached_source_file_id(file_hash, existing_file.id)
            return _source_file_to_oferta(existing_file)

    from fastapi.concurrency import run_in_threadpool

    try:
        oferta = await run_in_threadpool(
            extractor.extract_from_bytes, content, file.filename or "document.pdf"
        )
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falló la extracción: {str(e)}")

    try:
        carrera_clean = (carrera or "").strip() or None
        new_source = SourceFile(
            filename=file.filename or "document.pdf",
            file_hash=file_hash,
            carrera=carrera_clean,
        )
        session.add(new_source)

        for materia in oferta.materias:
            db_course = Course(
                nrc=materia.nrc or "",
                course_code=materia.clave or "",
                group_code=materia.grupo or "",
                subject_name=materia.nombre,
                professor=materia.profesor,
                credits=materia.creditos,
                source_file=new_source,
            )

            for h in materia.horarios:
                try:
                    start_parts = h.hora_inicio.split(":")
                    end_parts = h.hora_fin.split(":")
                    t_start = time(int(start_parts[0]), int(start_parts[1]))
                    t_end = time(int(end_parts[0]), int(end_parts[1]))
                except (ValueError, IndexError):
                    t_start = time(0, 0)
                    t_end = time(0, 0)

                try:
                    dia_enum = DayEnum(h.dia)
                except ValueError:
                    continue

                slot = TimeSlot(
                    day=dia_enum,
                    start_time=t_start,
                    end_time=t_end,
                    classroom=h.aula,
                )
                db_course.time_slots.append(slot)

            session.add(db_course)

        session.commit()
        session.refresh(new_source)
        set_cached_source_file_id(file_hash, new_source.id)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando en BD: {str(e)}")

    return oferta


@router.post("/upload-mapa", response_model=MapaCurricularExtraido)
async def upload_mapa_curricular(
    file: UploadFile | None = File(None, description="PDF del mapa curricular"),
) -> MapaCurricularExtraido:
    """Sube un PDF de mapa curricular y extrae las materias del plan."""
    if file is None or not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Falta el archivo. Envie como multipart/form-data con campo 'file'.",
        )
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Se requiere un archivo PDF")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Límite {settings.max_upload_mb} MB")
    return parser_mapa.parsear_desde_bytes(content, file.filename or "mapa.pdf")
