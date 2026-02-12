"""Esquemas Pydantic para request/response de la API."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


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
    Una fila de oferta BUAP: un registro por (NRC, Materia, Secc, Dia, Hora, Profesor, Salon).
    Formato objetivo: NRC, Clave, Materia, Secc, Dias, Hora, Profesor, Salon.
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
        """Clave sin espacios para cruce con plan (ej. ITIS601)."""
        return (self.clave or "").replace(" ", "").strip().upper()

    @computed_field
    @property
    def hora(self) -> str:
        """Rango de hora en formato militar ej. 1000-1059."""
        hi = (self.hora_inicio or "").replace(":", "").strip()
        hf = (self.hora_fin or "").replace(":", "").strip()
        return f"{hi}-{hf}" if hi and hf else ""


class HorarioSlot(BaseModel):
    """Un bloque de horario (día + hora inicio/fin)."""

    dia: str = Field(..., description="Día de la semana (Lunes, Martes, etc.)")
    hora_inicio: str = Field(..., description="Hora de inicio ej. 07:00")
    hora_fin: str = Field(..., description="Hora de fin ej. 08:30")


def _clave_normalizada(clave: Optional[str]) -> str:
    """Clave sin espacios en mayúsculas para cruce con mapa curricular."""
    return (clave or "").replace(" ", "").strip().upper()


class MateriaExtraida(BaseModel):
    """Materia obtenida tras extracción del PDF (agrupada, con varios horarios)."""

    nombre: str = Field(..., description="Nombre de la materia")
    clave: Optional[str] = Field(None, description="Clave de la materia")
    grupo: Optional[str] = Field(None, description="Número o id de grupo / sección")
    horarios: list[HorarioSlot] = Field(default_factory=list)
    profesor: Optional[str] = None
    aula: Optional[str] = None
    creditos: Optional[int] = None

    @computed_field
    @property
    def clave_normalizada(self) -> str:
        """Clave sin espacios para cruce con plan (ej. ITIS601)."""
        return _clave_normalizada(self.clave)


class OfertaExtraida(BaseModel):
    """
    Resultado de extraer un PDF de oferta BUAP.
    - filas: una entrada por cada combinación NRC/Clave/Materia/Secc/Dias/Hora/Profesor/Salon.
    - materias: vista agrupada por materia (para horarios y export).
    - archivos_procesados: nombres de PDF procesados.
    """

    filas: list[FilaOferta] = Field(
        default_factory=list,
        description="Filas extraídas: NRC, Clave, Materia, Secc, Dias, Hora, Profesor, Salon",
    )
    materias: list[MateriaExtraida] = Field(default_factory=list)
    archivos_procesados: list[str] = Field(default_factory=list)


class ScheduleOption(BaseModel):
    """Una opción de horario (combinación de grupos sin traslape)."""

    materias: list[MateriaExtraida] = Field(default_factory=list)
    score: Optional[float] = Field(None, description="Puntuación o criterio de calidad")


class MateriaPlan(BaseModel):
    """
    Materia del plan de estudios (mapa curricular).

    En cada bloque del mapa suelen aparecer: nombre y cuatro números según la leyenda:
    Horas de Teoría, Horas de Laboratorio, Horas de Trabajo Independiente, Número de Créditos.
    """

    clave: str = Field(..., description="Clave ej. ITIS 601")
    nombre: str = Field(..., description="Nombre de la materia")
    creditos: Optional[int] = Field(None, description="Número de créditos (4to número del bloque)")
    horas_teoria: Optional[int] = Field(None, description="Horas de teoría (1er número)")
    horas_lab: Optional[int] = Field(None, description="Horas de laboratorio (2do número)")
    horas_trabajo_indep: Optional[int] = Field(None, description="Horas de trabajo independiente (3er número)")
    periodo: Optional[int] = Field(None, description="Semestre/periodo sugerido")
    area: Optional[str] = Field(None, description="Área temática si aplica")

    @computed_field
    @property
    def clave_normalizada(self) -> str:
        return _clave_normalizada(self.clave)


class MapaCurricularExtraido(BaseModel):
    """Resultado de extraer un PDF de mapa curricular."""

    materias: list[MateriaPlan] = Field(default_factory=list)
    archivos_procesados: list[str] = Field(default_factory=list)
    advertencia: Optional[str] = Field(
        None,
        description="Ej. si el PDF es solo imagen y no se pudo extraer texto.",
    )


class MeterMateriasRequest(BaseModel):
    """Request para filtrar oferta por materias del plan (meter materias)."""

    claves_plan: list[str] = Field(
        ...,
        description="Claves del plan a inscribir (ej. ['ITIS 601', 'CCOS 260']). Se comparan sin espacios.",
    )
    oferta: OfertaExtraida = Field(..., description="Oferta ya extraída del PDF de oferta.")


class MeterMateriasResponse(BaseModel):
    """Materias de la oferta que coinciden con el plan (para inscribir)."""

    materias_coincidentes: list[MateriaExtraida] = Field(default_factory=list)
    claves_sin_oferta: list[str] = Field(
        default_factory=list,
        description="Claves del plan que no aparecen en la oferta.",
    )


class ExportFormat(str, Enum):
    """Formatos de exportación soportados."""

    PDF = "pdf"
    ICS = "ics"
    GOOGLE_CALENDAR = "google_calendar"
