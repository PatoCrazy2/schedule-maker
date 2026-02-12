from app.models.schemas import (
<<<<<<< HEAD
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
=======
>>>>>>> e40962f (refactor: update docker-compose and backend configuration; remove frontend Dockerfile)
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
<<<<<<< HEAD
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
=======
)

__all__ = [
>>>>>>> e40962f (refactor: update docker-compose and backend configuration; remove frontend Dockerfile)
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
<<<<<<< HEAD
    "normalizar_hora_militar",
=======
>>>>>>> e40962f (refactor: update docker-compose and backend configuration; remove frontend Dockerfile)
]
