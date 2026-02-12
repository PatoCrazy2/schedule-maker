"""
Orquestador de parsing de oferta: lee PDF y aplica el parser adecuado.

Inspirado en contable ParserEstadoCuenta. Procesamiento 100% local.
Devuelve filas en formato BUAP (NRC, Clave, Materia, Secc, Dias, Hora, Profesor, Salon)
y materias agrupadas para horarios/export.
"""
import logging
from pathlib import Path

from app.models.schemas import OfertaExtraida
from app.services.lector_pdf import LectorPDF, ContenidoPDF
from app.services.normalizador import normalizar_oferta
from app.services.parser_factory import ParserFactory
from app.services.parsers.banner_parser import _filas_a_materias

logger = logging.getLogger(__name__)


class ParserOferta:
    """Lee un PDF de oferta y extrae filas BUAP + materias usando el parser correspondiente."""

    def __init__(self) -> None:
        self.lector = LectorPDF()
        self.factory = ParserFactory()

    def parsear_desde_ruta(self, file_path: Path) -> OfertaExtraida:
        """Lee el PDF en file_path y devuelve OfertaExtraida (filas + materias)."""
        contenido = self.lector.leer(file_path)
        return self._parsear(contenido, file_path.name)

    def parsear_desde_bytes(self, contenido_bytes: bytes, nombre_archivo: str = "document.pdf") -> OfertaExtraida:
        """Parsea desde bytes (p. ej. upload)."""
        contenido = self.lector.leer_desde_bytes(contenido_bytes)
        return self._parsear(contenido, nombre_archivo)

    def _parsear(self, contenido: ContenidoPDF, nombre_archivo: str) -> OfertaExtraida:
        parser = self.factory.obtener_parser(contenido, nombre_archivo)
        if not parser:
            logger.warning("Ningún parser pudo procesar %s; devolviendo vacío", nombre_archivo)
            return OfertaExtraida(archivos_procesados=[nombre_archivo])
        logger.info("Parser elegido para %s: %s", nombre_archivo, type(parser).__name__)
        filas = parser.extraer_filas(contenido, nombre_archivo)
        materias = _filas_a_materias(filas) if filas else parser.extraer_materias(contenido, nombre_archivo)
        oferta = OfertaExtraida(
            filas=filas,
            materias=materias,
            archivos_procesados=[nombre_archivo],
        )
        return normalizar_oferta(oferta)
