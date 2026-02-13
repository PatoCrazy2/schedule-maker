from app.models.schemas import (
    # --- New clean models ---
    DayEnum,
    TimeSlotBase,
    CourseBase,
    ExtractedTimeSlot,
    ExtractedCourse,
    TimeSlotRead,
    CourseRead,
    PlanRequirement,
    ScheduleMatchResponse,
    # --- Legacy models (backward compat) ---
    FilaOferta,
    MateriaExtraida,
    MateriaPlan,
    MapaCurricularExtraido,
    MeterMateriasRequest,
    MeterMateriasResponse,
    HorarioSlot,
    OfertaExtraida,
    ScheduleOption,
    ExportFormat,
    normalizar_hora_militar,
)

__all__ = [
    # New
    "DayEnum",
    "TimeSlotBase",
    "CourseBase",
    "ExtractedTimeSlot",
    "ExtractedCourse",
    "TimeSlotRead",
    "CourseRead",
    "PlanRequirement",
    "ScheduleMatchResponse",
    # Legacy
    "FilaOferta",
    "MateriaExtraida",
    "MateriaPlan",
    "MapaCurricularExtraido",
    "MeterMateriasRequest",
    "MeterMateriasResponse",
    "HorarioSlot",
    "OfertaExtraida",
    "ScheduleOption",
    "ExportFormat",
    "normalizar_hora_militar",
]
