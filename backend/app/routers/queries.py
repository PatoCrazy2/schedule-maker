from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, SQLModel
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.db_models import Course, SourceFile
from app.models.schemas import CourseResponse, SubjectResponse

router = APIRouter(prefix="/v1/files", tags=["Consultas de Archivo"])


@router.get("/{file_hash}/subjects", response_model=List[SubjectResponse])
def get_file_subjects(
    file_hash: str, session: Session = Depends(get_session)
) -> List[SubjectResponse]:
    """Obtener nombres de materias (únicos) para un archivo dado."""
    source_file = session.exec(
        select(SourceFile).where(SourceFile.file_hash == file_hash)
    ).first()

    if not source_file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    stmt = (
        select(Course.subject_name)
        .where(Course.source_file_id == source_file.id)
        .distinct()
        .order_by(Course.subject_name)
    )
    subjects = session.exec(stmt).all()

    return [SubjectResponse(name=s) for s in subjects if s]


@router.get("/{file_hash}/courses", response_model=List[CourseResponse])
def get_file_courses(
    file_hash: str,
    subject_name: Optional[str] = Query(None, description="Filtro opcional por materia"),
    session: Session = Depends(get_session),
) -> List[CourseResponse]:
    """Obtener todos los cursos y sus horarios para un archivo dado. Filtro opcional por materia."""
    source_file = session.exec(
        select(SourceFile).where(SourceFile.file_hash == file_hash)
    ).first()

    if not source_file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    stmt = (
        select(Course)
        .where(Course.source_file_id == source_file.id)
        .options(selectinload(Course.time_slots))
    )

    if subject_name:
        stmt = stmt.where(Course.subject_name == subject_name)

    courses = session.exec(stmt).all()
    return list(courses)


class SourceFileSearchResponse(SQLModel):
    file_hash: str
    filename: str
    carrera: Optional[str] = None
    facultad: Optional[str] = None
    campus: Optional[str] = None
    periodo: Optional[str] = None


@router.get("/search", response_model=List[SourceFileSearchResponse])
def search_files(
    q: str = Query("", description="Nombre de carrera, campus, o archivo a buscar"),
    session: Session = Depends(get_session)
):
    """Busca archivos fuente por coincidencia de texto en varios campos (carrera, filename, etc)."""
    stmt = select(SourceFile)
    if q:
        search = f"%{q}%"
        stmt = stmt.where(
            (SourceFile.carrera.ilike(search)) |
            (SourceFile.filename.ilike(search)) |
            (SourceFile.facultad.ilike(search)) |
            (SourceFile.campus.ilike(search)) |
            (SourceFile.periodo.ilike(search))
        )
    stmt = stmt.order_by(SourceFile.processed_at.desc()).limit(20)
    files = session.exec(stmt).all()
    return files


@router.get("/{file_hash}/oferta")
def get_file_oferta(file_hash: str, session: Session = Depends(get_session)):
    """Obtiene la OfertaExtraida dado un file_hash."""
    from app.routers.pdf import _source_file_to_oferta
    
    source_file = session.exec(
        select(SourceFile).where(SourceFile.file_hash == file_hash)
    ).first()
    
    if not source_file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
    return _source_file_to_oferta(source_file)
