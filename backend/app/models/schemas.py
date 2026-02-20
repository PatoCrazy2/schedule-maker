"""Esquemas Pydantic para request/response de la API."""
from datetime import datetime, time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class DayEnum(str, Enum):
    """Códigos de día BUAP."""
    MONDAY = "L"
    TUESDAY = "A"
    WEDNESDAY = "M"
    THURSDAY = "J"
    FRIDAY = "V"
    SATURDAY = "S"
    SUNDAY = "D"


def normalizar_hora_militar(s: str) -> str:
    """Convierte 1000 -> 10:00, 1059 -> 10:59."""
    s = (s or "").strip().replace(":", "")
    if not s or len(s) < 3:
        return s
    if len(s) == 4 and s.isdigit():
        return f"{s[:2]}:{s[2:]}"
    return s


def _clave_normalizada(clave: Optional[str]) -> str:
    return (clave or "").replace(" ", "").strip().upper()


class FilaOferta(BaseModel):
    """Una fila de oferta BUAP."""
    nrc: str = Field(..., description="NRC (ej. 50030)")
    clave: str = Field(..., description="Clave de materia (ej. CCOS 260)")
    materia: str = Field(..., description="Nombre de la materia")
    secc: str = Field(..., description="Sección (ej. OO1)")
    dias: str = Field(..., description="Día(s): L, A, J, M, etc.")
    hora_inicio: str = Field(..., description="Hora inicio ej. 10:00")
    hora_fin: str = Field(..., description="Hora fin ej. 10:59")
    profesor: str = Field(..., description="Nombre del profesor")
    salon: str = Field(..., description="Salón (ej. 1CCO4/305)")

    @computed_field
    @property
    def clave_normalizada(self) -> str:
        return _clave_normalizada(self.clave)

    @computed_field
    @property
    def hora(self) -> str:
        hi = (self.hora_inicio or "").replace(":", "").strip()
        hf = (self.hora_fin or "").replace(":", "").strip()
        return f"{hi}-{hf}" if hi and hf else ""


class HorarioSlot(BaseModel):
    """Un bloque de horario (día + hora inicio/fin + salón)."""
    dia: str = Field(..., description="Día de la semana (L, A, M, J, V, S, D)")
    hora_inicio: str = Field(..., description="Hora de inicio ej. 07:00")
    hora_fin: str = Field(..., description="Hora de fin ej. 08:30")
    aula: Optional[str] = Field(None, description="Salón (ej. 1CCO4/305)")


class MateriaExtraida(BaseModel):
    """Materia obtenida tras extracción del PDF (agrupada)."""
    nrc: Optional[str] = Field(None, description="NRC de la materia")
    nombre: str = Field(..., description="Nombre de la materia")
    clave: Optional[str] = Field(None, description="Clave de la materia")
    grupo: Optional[str] = Field(None, description="Sección / grupo")
    horarios: list[HorarioSlot] = Field(default_factory=list)
    profesor: Optional[str] = None
    creditos: Optional[int] = None
    aula: Optional[str] = None

    @computed_field
    @property
    def clave_normalizada(self) -> str:
        return _clave_normalizada(self.clave)


class OfertaExtraida(BaseModel):
    """Resultado de extraer un PDF de oferta BUAP."""
    filas: list[FilaOferta] = Field(default_factory=list)
    materias: list[MateriaExtraida] = Field(default_factory=list)
    archivos_procesados: list[str] = Field(default_factory=list)


class ScheduleOption(BaseModel):
    """Una opción de horario (combinación sin traslape)."""
    materias: list[MateriaExtraida] = Field(default_factory=list)
    score: Optional[float] = Field(None)


class MateriaPlan(BaseModel):
    """Materia del plan de estudios (mapa curricular)."""
    clave: str = Field(..., description="Clave ej. ITIS 601")
    nombre: str = Field(..., description="Nombre de la materia")
    creditos: Optional[int] = Field(None)
    horas_teoria: Optional[int] = Field(None)
    horas_lab: Optional[int] = Field(None)
    horas_trabajo_indep: Optional[int] = Field(None)
    periodo: Optional[int] = Field(None)
    area: Optional[str] = Field(None)

    @computed_field
    @property
    def clave_normalizada(self) -> str:
        return _clave_normalizada(self.clave)


class MapaCurricularExtraido(BaseModel):
    """Resultado de extraer un PDF de mapa curricular."""
    materias: list[MateriaPlan] = Field(default_factory=list)
    archivos_procesados: list[str] = Field(default_factory=list)
    advertencia: Optional[str] = Field(None)


class MeterMateriasRequest(BaseModel):
    """Request para filtrar oferta por materias del plan."""
    claves_plan: list[str] = Field(...)
    oferta: OfertaExtraida = Field(...)


class MeterMateriasResponse(BaseModel):
    """Materias de la oferta que coinciden con el plan."""
    materias_coincidentes: list[MateriaExtraida] = Field(default_factory=list)
    claves_sin_oferta: list[str] = Field(default_factory=list)


class ExportFormat(str, Enum):
    """Formatos de exportación soportados."""
    PDF = "pdf"
    ICS = "ics"
    GOOGLE_CALENDAR = "google_calendar"


# --- Instrumento de evaluacion docente (escala 1-5) ---
# 1=Muy deficiente, 2=Deficiente, 3=Aceptable, 4=Bueno, 5=Excelente

class ProfessorReviewCreate(BaseModel):
    """Request para crear evaluacion docente."""
    professor_name: str = Field(..., min_length=1)
    materia_nombre: Optional[str] = None
    dominio_contenido: Optional[int] = Field(None, ge=1, le=5)
    claridad: Optional[int] = Field(None, ge=1, le=5)
    metodologia: Optional[int] = Field(None, ge=1, le=5)
    justicia_evaluacion: Optional[int] = Field(None, ge=1, le=5)
    exigencia: Optional[int] = Field(None, ge=1, le=5)
    apoyo: Optional[int] = Field(None, ge=1, le=5)
    organizacion: Optional[int] = Field(None, ge=1, le=5)
    impacto: Optional[int] = Field(None, ge=1, le=5)
    justificacion_dominio: Optional[str] = Field(None, max_length=1000)
    justificacion_claridad: Optional[str] = Field(None, max_length=1000)
    justificacion_metodologia: Optional[str] = Field(None, max_length=1000)
    justificacion_justicia: Optional[str] = Field(None, max_length=1000)
    justificacion_exigencia: Optional[str] = Field(None, max_length=1000)
    justificacion_apoyo: Optional[str] = Field(None, max_length=1000)
    justificacion_organizacion: Optional[str] = Field(None, max_length=1000)
    justificacion_impacto: Optional[str] = Field(None, max_length=1000)
    comentario_general: Optional[str] = Field(None, max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class ProfessorReviewRead(BaseModel):
    """Evaluacion docente (respuesta)."""
    id: int
    professor_name: str
    materia_nombre: Optional[str] = None
    dominio_contenido: Optional[int] = None
    claridad: Optional[int] = None
    metodologia: Optional[int] = None
    justicia_evaluacion: Optional[int] = None
    exigencia: Optional[int] = None
    apoyo: Optional[int] = None
    organizacion: Optional[int] = None
    impacto: Optional[int] = None
    justificacion_dominio: Optional[str] = None
    justificacion_claridad: Optional[str] = None
    justificacion_metodologia: Optional[str] = None
    justificacion_justicia: Optional[str] = None
    justificacion_exigencia: Optional[str] = None
    justificacion_apoyo: Optional[str] = None
    justificacion_organizacion: Optional[str] = None
    justificacion_impacto: Optional[str] = None
    comentario_general: Optional[str] = None
    promedio: Optional[float] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfessorRatingResponse(BaseModel):
    """Promedio y lista de evaluaciones para un profesor."""
    professor_name: str
    average_rating: float
    total_reviews: int
    reviews: List[ProfessorReviewRead] = Field(default_factory=list)


class ProfessorCourseDetail(BaseModel):
    """Materia/course de un profesor con NRC y datos."""
    nrc: str
    clave: str
    nombre: str
    grupo: str
    horarios: List[HorarioSlot] = Field(default_factory=list)


class ProfessorListItem(BaseModel):
    """Profesor con materias y resumen de evaluaciones."""
    name: str
    materias: List[str] = Field(default_factory=list)
    courses: List[ProfessorCourseDetail] = Field(default_factory=list)
    average_rating: float
    total_reviews: int
