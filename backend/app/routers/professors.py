"""Endpoints para evaluacion docente."""
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.db_models import Course, ProfessorReview, SourceFile
from app.models.schemas import (
    HorarioSlot,
    ProfessorCourseDetail,
    ProfessorListItem,
    ProfessorRatingResponse,
    ProfessorReviewCreate,
    ProfessorReviewRead,
)

router = APIRouter(prefix="/professors", tags=["Profesores"])


def _promedio_review(r: ProfessorReview) -> float:
    """Promedio de las 8 metricas. Fallback a rating si no hay metricas."""
    vals = [
        r.dominio_contenido, r.claridad, r.metodologia, r.justicia_evaluacion,
        r.exigencia, r.apoyo, r.organizacion, r.impacto,
    ]
    nums = [v for v in vals if v is not None]
    if nums:
        return round(sum(nums) / len(nums), 1)
    return float(r.rating or 0)


def _review_to_read(r: ProfessorReview) -> ProfessorReviewRead:
    d = ProfessorReviewRead.model_validate(r)
    d.promedio = _promedio_review(r)
    return d


@router.post("/reviews", response_model=ProfessorReviewRead)
def create_review(
    body: ProfessorReviewCreate,
    session: Session = Depends(get_session),
) -> ProfessorReviewRead:
    """Crear evaluacion docente con instrumento formal."""
    review = ProfessorReview(
        professor_name=body.professor_name.strip(),
        materia_nombre=(body.materia_nombre or "").strip() or None,
        dominio_contenido=body.dominio_contenido,
        claridad=body.claridad,
        metodologia=body.metodologia,
        justicia_evaluacion=body.justicia_evaluacion,
        exigencia=body.exigencia,
        apoyo=body.apoyo,
        organizacion=body.organizacion,
        impacto=body.impacto,
        justificacion_dominio=(body.justificacion_dominio or "").strip() or None,
        justificacion_claridad=(body.justificacion_claridad or "").strip() or None,
        justificacion_metodologia=(body.justificacion_metodologia or "").strip() or None,
        justificacion_justicia=(body.justificacion_justicia or "").strip() or None,
        justificacion_exigencia=(body.justificacion_exigencia or "").strip() or None,
        justificacion_apoyo=(body.justificacion_apoyo or "").strip() or None,
        justificacion_organizacion=(body.justificacion_organizacion or "").strip() or None,
        justificacion_impacto=(body.justificacion_impacto or "").strip() or None,
        comentario_general=(body.comentario_general or "").strip() or None,
        rating=body.rating,
        comment=(body.comment or "").strip() or None,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return _review_to_read(review)


def _course_to_detail(c: Course) -> ProfessorCourseDetail:
    horarios = [
        HorarioSlot(
            dia=slot.day.value,
            hora_inicio=slot.start_time.strftime("%H:%M"),
            hora_fin=slot.end_time.strftime("%H:%M"),
            aula=slot.classroom,
        )
        for slot in c.time_slots
    ]
    return ProfessorCourseDetail(
        nrc=c.nrc or "",
        clave=c.course_code or "",
        nombre=c.subject_name or "",
        grupo=c.group_code or "",
        horarios=horarios,
    )


@router.get("/list", response_model=list[ProfessorListItem])
def list_professors(session: Session = Depends(get_session)) -> list[ProfessorListItem]:
    """
    Lista todos los profesores registrados (desde Course) con materias, NRC y evaluaciones.
    """
    stmt = select(Course).where(Course.professor != None, Course.professor != "")
    courses = list(session.exec(stmt).all())

    prof_courses: dict[str, list[Course]] = defaultdict(list)
    for c in courses:
        if c.professor:
            prof_courses[c.professor].append(c)

    result = []
    for name in sorted(prof_courses.keys()):
        prof_courses_list = prof_courses[name]
        materias_set = {c.subject_name or "" for c in prof_courses_list if c.subject_name}
        materias = sorted([m for m in materias_set if m])
        courses_detail = [_course_to_detail(c) for c in prof_courses_list]

        stmt_rev = select(ProfessorReview).where(ProfessorReview.professor_name == name)
        reviews = list(session.exec(stmt_rev).all())
        if reviews:
            promedios = [_promedio_review(r) for r in reviews]
            avg = round(sum(promedios) / len(promedios), 1)
        else:
            avg = 0.0
        result.append(
            ProfessorListItem(
                name=name,
                materias=materias,
                courses=courses_detail,
                average_rating=avg,
                total_reviews=len(reviews),
            )
        )
    return result


@router.get("/ratings/batch")
def get_ratings_batch(
    names: list[str] = Query(..., description="Nombres de profesores"),
    session: Session = Depends(get_session),
) -> dict[str, dict]:
    """Obtener promedio para varios profesores (usa promedio de 8 metricas)."""
    result: dict[str, dict] = {}
    for name in names:
        if not name or name in result:
            continue
        stmt = select(ProfessorReview).where(ProfessorReview.professor_name == name)
        reviews = list(session.exec(stmt).all())
        if not reviews:
            result[name] = {"average_rating": 0.0, "total_reviews": 0}
        else:
            proms = [_promedio_review(r) for r in reviews]
            result[name] = {
                "average_rating": round(sum(proms) / len(proms), 1),
                "total_reviews": len(reviews),
            }
    return result


@router.get("/{professor_name}/reviews", response_model=ProfessorRatingResponse)
def get_professor_reviews(
    professor_name: str,
    session: Session = Depends(get_session),
) -> ProfessorRatingResponse:
    """Obtener evaluaciones y promedio de un profesor."""
    stmt = select(ProfessorReview).where(
        ProfessorReview.professor_name == professor_name
    ).order_by(ProfessorReview.created_at.desc())
    reviews = list(session.exec(stmt).all())

    if not reviews:
        return ProfessorRatingResponse(
            professor_name=professor_name,
            average_rating=0.0,
            total_reviews=0,
            reviews=[],
        )

    proms = [_promedio_review(r) for r in reviews]
    avg = round(sum(proms) / len(proms), 1)

    return ProfessorRatingResponse(
        professor_name=professor_name,
        average_rating=avg,
        total_reviews=len(reviews),
        reviews=[_review_to_read(r) for r in reviews],
    )
