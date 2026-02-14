"""
Esquemas Pydantic para request/response de la API.

Organización:
  1. ENUMS & BASES  — DayEnum, TimeSlotBase, CourseBase (nuevos, limpios)
  2. MODELOS DE EXTRACCIÓN (INPUT/PDF) — ExtractedTimeSlot, ExtractedCourse
  3. MODELOS DE RESPUESTA (OUTPUT/API) — TimeSlotRead, CourseRead, ScheduleMatchResponse
  4. LOGIC MODELS — PlanRequirement
  5. LEGACY MODELS — FilaOferta, HorarioSlot, MateriaExtraida, etc. (compatibilidad)
"""
from enum import Enum
from typing import List, Optional
from datetime import time

from pydantic import BaseModel, Field, ConfigDict, computed_field, model_validator


# ═══════════════════════════════════════════════════════════════
# 1. ENUMS & BASES
# ═══════════════════════════════════════════════════════════════

class DayEnum(str, Enum):
    """Códigos de día BUAP."""
    MONDAY    = "L"
    TUESDAY   = "A"   # BUAP usa 'A' para Martes
    WEDNESDAY = "M"   # BUAP usa 'M' para Miércoles
    THURSDAY  = "J"
    FRIDAY    = "V"
    SATURDAY  = "S"
    SUNDAY    = "D"


class TimeSlotBase(BaseModel):
    """Base común para TimeSlot (sin ID). El salón pertenece al slot."""
    day: DayEnum
    start_time: time
    end_time: time
    classroom: Optional[str] = None

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class CourseBase(BaseModel):
    """Base común para Curso (sin ID ni lista de horarios)."""
    nrc: str
    course_code: str       # Clave (ej: CCOS 260)
    group_code: str        # Sección/Grupo (ej: 001)
    subject_name: str      # Nombre de la materia
    professor: Optional[str] = None
    credits: Optional[int] = None


# ═══════════════════════════════════════════════════════════════
# 2. MODELOS DE EXTRACCIÓN (INPUT / PDF ENGINE)
#    Usados por el motor de PDF. NO tienen ID.
# ═══════════════════════════════════════════════════════════════

class ExtractedTimeSlot(TimeSlotBase):
    """Usado por el parser para crear horarios en memoria."""
    pass


class ExtractedCourse(CourseBase):
    """Usado por el parser. Contiene la lista de horarios extraídos."""
    schedule: List[ExtractedTimeSlot] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# 3. MODELOS DE RESPUESTA (OUTPUT / API)
#    Usados por los endpoints. SÍ tienen ID.
# ═══════════════════════════════════════════════════════════════

class TimeSlotRead(TimeSlotBase):
    """Slot de horario con ID (respuesta de API)."""
    id: int
    model_config = ConfigDict(from_attributes=True)


class CourseRead(CourseBase):
    """Curso con ID y lista de slots de horario (respuesta de API)."""
    id: int
    time_slots: List[TimeSlotRead] = Field(default_factory=list)

    @property
    def normalized_code(self) -> str:
        """Clave sin espacios para cruce con plan."""
        return self.course_code.replace(" ", "").upper()

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# 4. LOGIC MODELS (Para el algoritmo de 'Meter Materias')
# ═══════════════════════════════════════════════════════════════

class PlanRequirement(BaseModel):
    """Materia requerida por el plan de estudios."""
    course_code: str
    required: bool = True


class ScheduleMatchResponse(BaseModel):
    """Respuesta del endpoint inteligente de cruce oferta/plan."""
    found_courses: List[CourseRead]
    missing_codes: List[str]
    conflicts: List[str]   # Ej: "Física choca con Cálculo"


# ═══════════════════════════════════════════════════════════════
# 5. LEGACY MODELS — Compatibilidad con parsers/normalizadores
#    Estos modelos serán reemplazados gradualmente por los de
#    arriba conforme se migren los parsers.
# ═══════════════════════════════════════════════════════════════

def normalizar_hora_militar(s: str) -> str:
    """Convierte 1000 -> 10:00, 1059 -> 10:59."""
    s = (s or "").strip().replace(":", "")
    if not s or len(s) < 3:
        return s
    if len(s) == 4 and s.isdigit():
        return f"{s[:2]}:{s[2:]}"
    return s


class FilaOferta(BaseModel):
    """
    [LEGACY] Una fila de oferta BUAP: un registro por (NRC, Materia, Secc, Dia, Hora, Profesor, Salon).
    """
    nrc: str = Field(..., description="NRC (ej. 50030)")
    clave: str = Field(..., description="Clave de materia (ej. CCOS 260)")
    materia: str = Field(..., description="Nombre de la materia")
    secc: str = Field(..., description="Sección (ej. OO1)")
    dias: str = Field(..., description="Día(s): L, A, J, M, etc.")
    hora_inicio: str = Field(..., description="Hora inicio normalizada ej. 10:00")
    hora_fin: str = Field(..., description="Hora fin normalizada ej. 10:59")
    profesor: str = Field(..., description="Nombre del profesor")
    salon: str = Field(..., description="Salón (ej. 1CCO4/305)")

    @computed_field
    @property
    def clave_normalizada(self) -> str:
        return (self.clave or "").replace(" ", "").strip().upper()

    @computed_field
    @property
    def hora(self) -> str:
        hi = (self.hora_inicio or "").replace(":", "").strip()
        hf = (self.hora_fin or "").replace(":", "").strip()
        return f"{hi}-{hf}" if hi and hf else ""


class HorarioSlot(BaseModel):
    """[LEGACY] Un bloque de horario (día + hora inicio/fin + salón)."""
    dia: str = Field(..., description="Día de la semana (Lunes, Martes, etc.)")
    hora_inicio: str = Field(..., description="Hora de inicio ej. 07:00")
    hora_fin: str = Field(..., description="Hora de fin ej. 08:30")
    aula: Optional[str] = Field(None, description="Salón (ej. 1CCO4/305)")


def _clave_normalizada(clave: Optional[str]) -> str:
    return (clave or "").replace(" ", "").strip().upper()


class MateriaExtraida(BaseModel):
    """[LEGACY] Materia obtenida tras extracción del PDF (agrupada)."""
    nrc: Optional[str] = Field(None, description="NRC de la materia")
    nombre: str = Field(..., description="Nombre de la materia")
    clave: Optional[str] = Field(None, description="Clave de la materia")
    grupo: Optional[str] = Field(None, description="Sección / grupo")
    horarios: list[HorarioSlot] = Field(default_factory=list)
    profesor: Optional[str] = None
    creditos: Optional[int] = None

    @computed_field
    @property
    def clave_normalizada(self) -> str:
        return _clave_normalizada(self.clave)


class OfertaExtraida(BaseModel):
    """[LEGACY] Resultado de extraer un PDF de oferta BUAP."""
    filas: list[FilaOferta] = Field(default_factory=list)
    materias: list[MateriaExtraida] = Field(default_factory=list)
    archivos_procesados: list[str] = Field(default_factory=list)


class ScheduleOption(BaseModel):
    """[LEGACY] Una opción de horario (combinación sin traslape)."""
    materias: list[MateriaExtraida] = Field(default_factory=list)
    score: Optional[float] = Field(None)


class MateriaPlan(BaseModel):
    """[LEGACY] Materia del plan de estudios (mapa curricular)."""
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
    """[LEGACY] Resultado de extraer un PDF de mapa curricular."""
    materias: list[MateriaPlan] = Field(default_factory=list)
    archivos_procesados: list[str] = Field(default_factory=list)
    advertencia: Optional[str] = Field(None)


class MeterMateriasRequest(BaseModel):
    """[LEGACY] Request para filtrar oferta por materias del plan."""
    claves_plan: list[str] = Field(...)
    oferta: OfertaExtraida = Field(...)


class MeterMateriasResponse(BaseModel):
    """[LEGACY] Materias de la oferta que coinciden con el plan."""
    materias_coincidentes: list[MateriaExtraida] = Field(default_factory=list)
    claves_sin_oferta: list[str] = Field(default_factory=list)


class ExportFormat(str, Enum):
    """Formatos de exportación soportados."""
    PDF = "pdf"
    ICS = "ics"
    GOOGLE_CALENDAR = "google_calendar"
