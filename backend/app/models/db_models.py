from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from app.models.schemas import DayEnum
from datetime import time, datetime


class SourceFile(SQLModel, table=True):
    __tablename__ = "source_file"
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    file_hash: str = Field(index=True, unique=True)
    facultad: Optional[str] = Field(default=None)
    carrera: Optional[str] = Field(default=None, index=True)
    campus: Optional[str] = Field(default=None)
    periodo: Optional[str] = Field(default=None)
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    courses: List["Course"] = Relationship(back_populates="source_file")


class Course(SQLModel, table=True):
    __tablename__ = "course"
    id: Optional[int] = Field(default=None, primary_key=True)
    nrc: str = Field(index=True)
    course_code: str
    group_code: str
    subject_name: str
    professor: Optional[str] = None
    credits: Optional[int] = None
    
    source_file_id: Optional[int] = Field(default=None, foreign_key="source_file.id")
    source_file: Optional[SourceFile] = Relationship(back_populates="courses")

    time_slots: List["TimeSlot"] = Relationship(back_populates="course")


class TimeSlot(SQLModel, table=True):
    __tablename__ = "time_slot"
    id: Optional[int] = Field(default=None, primary_key=True)
    day: DayEnum
    start_time: time
    end_time: time
    classroom: Optional[str] = None
    
    course_id: Optional[int] = Field(default=None, foreign_key="course.id")
    course: Optional[Course] = Relationship(back_populates="time_slots")


class ProfessorReview(SQLModel, table=True):
    """Instrumento formal de evaluacion docente (escala 1-5)."""
    __tablename__ = "professor_review"
    id: Optional[int] = Field(default=None, primary_key=True)
    professor_name: str = Field(index=True)
    materia_nombre: Optional[str] = Field(default=None, index=True)

    dominio_contenido: Optional[int] = Field(default=None, ge=1, le=5)
    claridad: Optional[int] = Field(default=None, ge=1, le=5)
    metodologia: Optional[int] = Field(default=None, ge=1, le=5)
    justicia_evaluacion: Optional[int] = Field(default=None, ge=1, le=5)
    exigencia: Optional[int] = Field(default=None, ge=1, le=5)
    apoyo: Optional[int] = Field(default=None, ge=1, le=5)
    organizacion: Optional[int] = Field(default=None, ge=1, le=5)
    impacto: Optional[int] = Field(default=None, ge=1, le=5)

    justificacion_dominio: Optional[str] = None
    justificacion_claridad: Optional[str] = None
    justificacion_metodologia: Optional[str] = None
    justificacion_justicia: Optional[str] = None
    justificacion_exigencia: Optional[str] = None
    justificacion_apoyo: Optional[str] = None
    justificacion_organizacion: Optional[str] = None
    justificacion_impacto: Optional[str] = None

    comentario_general: Optional[str] = None

    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
