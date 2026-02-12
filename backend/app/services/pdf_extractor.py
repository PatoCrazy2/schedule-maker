"""Servicio de extracción de oferta desde PDF usando lector + parser (patrón contable)."""
from pathlib import Path

from app.models.schemas import OfertaExtraida
from app.services.parser_oferta import ParserOferta


class PdfExtractorService:
    """Extrae oferta académica desde PDF: delega en LectorPDF y ParserOferta."""

    def __init__(self) -> None:
        self._parser = ParserOferta()

    def extract_from_path(self, file_path: Path) -> OfertaExtraida:
        """Extrae materias/horarios desde un PDF en la ruta dada."""
        return self._parser.parsear_desde_ruta(Path(file_path))

    def extract_from_bytes(self, content: bytes, filename: str = "document.pdf") -> OfertaExtraida:
        """Extrae desde bytes (p. ej. contenido de upload)."""
        return self._parser.parsear_desde_bytes(content, filename)
