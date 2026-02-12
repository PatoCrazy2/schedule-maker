"""
Factory para obtener el parser de oferta adecuado según el contenido/archivo.

Inspirado en contable ParserFactory: orden de parsers más específicos primero.
"""
from typing import Optional

from app.services.lector_pdf import ContenidoPDF
from app.services.parsers.base_parser import BaseOfertaParser
from app.services.parsers.banner_parser import BannerOfertaParser


class ParserFactory:
    """Devuelve el primer parser que pueda manejar el contenido."""

    def __init__(self) -> None:
        self.parsers: list[BaseOfertaParser] = [
            BannerOfertaParser(),
        ]

    def obtener_parser(
        self, contenido: ContenidoPDF, nombre_archivo: str = ""
    ) -> Optional[BaseOfertaParser]:
        """Obtiene el parser que puede procesar este PDF."""
        for parser in self.parsers:
            if parser.puede_parsear(contenido, nombre_archivo):
                return parser
        return None
