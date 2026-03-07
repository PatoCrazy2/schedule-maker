"""
Parser base para ofertas académicas (PDF BUAP / Banner).

Cada formato (Banner, mapas de carrera, etc.) puede tener un parser
que implemente esta interfaz.
"""
import re
from abc import ABC, abstractmethod

from app.models.schemas import FilaOferta, MateriaExtraida
from app.services.lector_pdf import ContenidoPDF


class BaseOfertaParser(ABC):
    """Interfaz para parsers de oferta académica."""

    def puede_parsear(self, contenido: ContenidoPDF, nombre_archivo: str = "") -> bool:
        texto = (contenido.texto_completo or "").upper()
        
        # 1. Verificación estricta: debe contener estrictamente TODAS las 8 palabras
        palabras_encontradas = set(re.findall(r"NRC|CLAVE|MATERIA|SECC|DIAS|HORA|PROFESOR|SALON", texto))
        if len(palabras_encontradas) != 8:
            return False
            
        # 2. Si no hay tablas, se rechaza inmediatamente
        if not contenido.tablas_por_pagina or not any(t for t in contenido.tablas_por_pagina):
            return False
            
        # 3. Validar estrictamente que la tabla tenga solo 8 columnas
        for pag in contenido.tablas_por_pagina:
            for tabla in pag:
                if tabla and len(tabla) > 0 and len(tabla[0]) == 8:
                    return True
                    
        return False

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

    def extraer_metadata(self, contenido: ContenidoPDF) -> dict:
        """
        Extrae metadata adicional del PDF. Por defecto vacío.
        Los parsers específicos pueden sobrescribir esto.
        """
        return {}
