"""Endpoints para generación de horarios y cruce oferta/plan."""
from fastapi import APIRouter

from app.models.schemas import (
    MeterMateriasRequest,
    MeterMateriasResponse,
    OfertaExtraida,
    ScheduleOption,
)
from app.services.normalizador import normalizar_clave

router = APIRouter(prefix="/schedules", tags=["Horarios"])


@router.post("/meter-materias", response_model=MeterMateriasResponse)
def meter_materias(body: MeterMateriasRequest) -> MeterMateriasResponse:
    """
    Filtra la oferta por las claves del plan que quieres inscribir ("meter materias").

    Entrada: **claves_plan** (ej. ["ITIS 601", "CCOS 260"]) y **oferta** (la respuesta
    de POST /api/pdf/upload). La comparación se hace por clave normalizada (sin espacios).

    Salida: **materias_coincidentes** (materias de la oferta que están en el plan) y
    **claves_sin_oferta** (claves del plan que no aparecen en la oferta).
    """
    claves_norm = {normalizar_clave(c) for c in body.claves_plan}
    coincidentes = [
        m for m in body.oferta.materias
        if m.clave_normalizada and m.clave_normalizada in claves_norm
    ]
    encontradas = {m.clave_normalizada for m in coincidentes}
    sin_oferta = [c for c in body.claves_plan if normalizar_clave(c) not in encontradas]
    return MeterMateriasResponse(
        materias_coincidentes=coincidentes,
        claves_sin_oferta=sin_oferta,
    )


@router.post("/options", response_model=list[ScheduleOption])
def get_schedule_options(oferta: OfertaExtraida) -> list[ScheduleOption]:
    """
    A partir de la oferta extraída, devuelve las mejores combinaciones
    de grupos sin traslape. Por ahora devuelve una opción por materia
    como placeholder; la lógica de conflictos se implementará después.
    """
    # Placeholder: una opción con todas las materias (sin detección de traslape aún)
    if not oferta.materias:
        return []

    # TODO: filtrar por materias seleccionadas, detectar traslapes, puntuar
    return [
        ScheduleOption(
            materias=oferta.materias,
            score=1.0,
        )
    ]
