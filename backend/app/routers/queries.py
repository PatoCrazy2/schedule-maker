from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
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
