"""Endpoints para exportar horario a PDF, ICS o Google Calendar."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models.schemas import ScheduleOption

router = APIRouter(prefix="/export", tags=["Exportar"])


def _schedule_to_ics(option: ScheduleOption) -> str:
    """Genera contenido ICS (compatible Apple Calendar y otros)."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Schedule Maker//BUAP//ES"]

    for m in option.materias:
        for h in m.horarios:
            summary = f"{m.nombre}" + (f" - {m.grupo}" if m.grupo else "")
            start = h.hora_inicio.replace(":", "") + "00" if len(h.hora_inicio) == 5 else h.hora_inicio.replace(":", "")
            end = h.hora_fin.replace(":", "") + "00" if len(h.hora_fin) == 5 else h.hora_fin.replace(":", "")
            lines.append("BEGIN:VEVENT")
            lines.append(f"SUMMARY:{summary}")
            lines.append(f"DTSTART;TZID=America/Mexico_City:20250101T{start}")
            lines.append(f"DTEND;TZID=America/Mexico_City:20250101T{end}")
            lines.append("RRULE:FREQ=WEEKLY")
            lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


@router.post("/ics")
def export_ics(option: ScheduleOption) -> Response:
    """Exporta el horario seleccionado como archivo .ics (Apple Calendar, etc.)."""
    content = _schedule_to_ics(option)
    return Response(
        content=content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=horario.ics"},
    )


@router.post("/pdf")
def export_pdf(option: ScheduleOption) -> None:
    """
    Exporta el horario como PDF.
    TODO: integrar generación real con reportlab o weasyprint.
    """
    raise HTTPException(status_code=501, detail="Exportación PDF en desarrollo")


@router.post("/google")
def export_google_calendar(option: ScheduleOption) -> dict:
    """
    Información para exportar a Google Calendar.
    TODO: OAuth y API de Google Calendar; por ahora se puede devolver
    un enlace o instrucciones para importar el ICS en Google.
    """
    ics_content = _schedule_to_ics(option)
    return {
        "message": "Usa el archivo ICS en Google Calendar: Calendario > Configuración > Importar",
        "ics_preview_length": len(ics_content),
    }
