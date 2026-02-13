"""
Parser base para ofertas académicas (PDF BUAP / Banner).

Cada formato (Banner, mapas de carrera, etc.) puede tener un parser
que implemente esta interfaz.
"""
from abc import ABC, abstractmethod

from app.models.schemas import FilaOferta, MateriaExtraida
from app.services.lector_pdf import ContenidoPDF


class BaseOfertaParser(ABC):
    """Interfaz para parsers de oferta académica."""

    @abstractmethod
    def puede_parsear(self, contenido: ContenidoPDF, nombre_archivo: str = "") -> bool:
        """Indica si este parser puede procesar el contenido/archivo dado."""
        pass

    def extraer_filas(
        self, contenido: ContenidoPDF, nombre_archivo: str = ""
    ) -> list[FilaOferta]:
        """
        Extrae filas en formato BUAP: NRC, Clave, Materia, Secc, Dias, Hora, Profesor, Salon.
        Por defecto vacío; los parsers pueden implementarlo.
        """
        return []

    @abstractmethod
    def extraer_materias(
        self, contenido: ContenidoPDF, nombre_archivo: str = ""
    ) -> list[MateriaExtraida]:
        """Extrae la lista de materias (con horarios) del contenido."""
        pass
