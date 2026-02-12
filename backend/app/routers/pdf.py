"""Endpoints para subida y extracción de PDF."""
from pathlib import Path

<<<<<<< HEAD
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends
from sqlmodel import Session, select
from datetime import time

from app.config import settings
from app.core.database import get_session
from app.models.schemas import MapaCurricularExtraido, OfertaExtraida, CourseRead, TimeSlotRead
from app.models.db_models import SourceFile, Course, TimeSlot
from app.services.ocr_pdf import ocr_disponible
from app.services.pdf_extractor import PdfExtractorService
from app.services.parser_mapa import ParserMapaCurricular
from app.utils.hashing import compute_file_hash
=======
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import settings
from app.models.schemas import MapaCurricularExtraido, OfertaExtraida
from app.services.ocr_pdf import ocr_disponible
from app.services.pdf_extractor import PdfExtractorService
from app.services.parser_mapa import ParserMapaCurricular
>>>>>>> e40962f (refactor: update docker-compose and backend configuration; remove frontend Dockerfile)

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
<<<<<<< HEAD
async def upload_and_extract(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
) -> OfertaExtraida:
    """
    Sube un PDF de oferta (ej. Banner BUAP) y extrae filas.
    
    Verifica si el archivo ya fue procesado (por hash). Si es así, retorna los datos de la BD.
    Si no, procesa el PDF, guarda los resultados en la BD y los retorna.
    """
    print(f"📥 Recibiendo archivo: {file.filename}")
    
=======
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
>>>>>>> e40962f (refactor: update docker-compose and backend configuration; remove frontend Dockerfile)
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Se requiere un archivo PDF")

    upload_dir = _ensure_upload_dir()
    size_mb = settings.max_upload_mb
<<<<<<< HEAD
    
    # Leer contenido
    try:
        content = await file.read()
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        raise HTTPException(status_code=400, detail="Error leyendo el archivo")

=======
    content = await file.read()
>>>>>>> e40962f (refactor: update docker-compose and backend configuration; remove frontend Dockerfile)
    if len(content) > size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {size_mb} MB",
        )

<<<<<<< HEAD
    # 1. Calcular Hash
    file_hash = compute_file_hash(content)
    print(f"🔑 Hash del archivo: {file_hash}")
    
    # 2. Buscar en BD
    try:
        # Usamos unique() para que cargue las relaciones correctamente si es necesario en versiones nuevas
        existing_file = session.exec(select(SourceFile).where(SourceFile.file_hash == file_hash)).first()
    except Exception as e:
        print(f"❌ Error consultando DB: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

    # Verificar si es un Cache Hit válido (tiene cursos guardados)
    if existing_file:
        if not existing_file.courses:
            print("⚠️ Archivo encontrado pero SIN cursos (Zombie Record). Re-procesando...")
            # Limpiamos el registro corrupto para re-procesar
            session.delete(existing_file)
            session.commit()
            existing_file = None
        else:
            print("⚡ Cache Hit! Retornando datos de la base de datos.")
            # Reconstruir OfertaExtraida desde la BD
            materias_recuperadas = []
            for course in existing_file.courses:
                horarios_legacy = []
                for slot in course.time_slots:
                    start_str = slot.start_time.strftime("%H:%M")
                    end_str = slot.end_time.strftime("%H:%M")
                    
                    from app.models.schemas import HorarioSlot
                    horarios_legacy.append(HorarioSlot(
                        dia=slot.day.value,
                        hora_inicio=start_str,
                        hora_fin=end_str,
                        aula=slot.classroom
                    ))
                
                from app.models.schemas import MateriaExtraida
                materia = MateriaExtraida(
                    nrc=course.nrc,
                    nombre=course.subject_name,
                    clave=course.course_code,
                    grupo=course.group_code,
                    profesor=course.professor,
                    creditos=course.credits,
                    horarios=horarios_legacy
                )
                materias_recuperadas.append(materia)
                
            return OfertaExtraida(
                filas=[],
                materias=materias_recuperadas,
                archivos_procesados=[existing_file.filename]
            )

    # 3. Cache Miss: Procesar PDF
    print("🐢 Cache Miss. Procesando PDF (esto puede tardar)...")
    from fastapi.concurrency import run_in_threadpool
    try:
        oferta = await run_in_threadpool(extractor.extract_from_bytes, content, file.filename or "document.pdf")
    except ValueError as ve:
        print(f"❌ Error de validación PDF: {ve}")
        # Retornamos 422 para indicar que el contenido no se pudo procesar (regla de negocio/parser)
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        print(f"❌ Error extrayendo PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Falló la extracción del PDF: {str(e)}")
    
    # 4. Guardar en BD (Transacción Atomica)
    print("💾 Guardando en base de datos...")
    try:
        # Crear SourceFile pero NO commitear aún
        new_source = SourceFile(filename=file.filename, file_hash=file_hash)
        session.add(new_source)
        
        for materia in oferta.materias:
            db_course = Course(
                nrc=materia.nrc or "",
                course_code=materia.clave or "",
                group_code=materia.grupo or "",
                subject_name=materia.nombre,
                professor=materia.profesor,
                credits=materia.creditos,
                # Enlace directo al objeto, SQLAlchemy resuelve el ID al commitear
                source_file=new_source 
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

                from app.models.schemas import DayEnum
                try:
                    dia_enum = DayEnum(h.dia)
                except ValueError:
                    continue

                slot = TimeSlot(
                    day=dia_enum,
                    start_time=t_start,
                    end_time=t_end,
                    classroom=h.aula
                )
                db_course.time_slots.append(slot)
            
            session.add(db_course)
        
        # Un solo commit al final. Si falla algo, no se guarda nada (ni el SourceFile).
        session.commit()
        session.refresh(new_source)
        print("✅ Guardado exitoso.")

    except Exception as e:
        print(f"❌ Error guardando en DB: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando en BD: {str(e)}")

    return oferta
=======
    return extractor.extract_from_bytes(content, file.filename or "document.pdf")

>>>>>>> e40962f (refactor: update docker-compose and backend configuration; remove frontend Dockerfile)

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
