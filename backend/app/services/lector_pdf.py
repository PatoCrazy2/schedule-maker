"""
Lector de PDF: extrae texto y tablas de forma local.

Inspirado en contable/app LectorDocumentos. Todo el procesamiento es local.
"""
import logging
from pathlib import Path
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)


class ContenidoPDF:
    """Resultado de leer un PDF: texto por página y tablas por página."""

    __slots__ = ("texto_completo", "tablas_por_pagina", "num_paginas")

    def __init__(
        self,
        texto_completo: str,
        tablas_por_pagina: list[list[list[Optional[str]]]],
        num_paginas: int,
    ):
        self.texto_completo = texto_completo
        self.tablas_por_pagina = tablas_por_pagina
        self.num_paginas = num_paginas


class LectorPDF:
    """Lee PDF locales y extrae texto y tablas con pdfplumber."""

    def leer(self, ruta_archivo: Path | str) -> ContenidoPDF:
        """
        Lee un PDF y devuelve texto y tablas.
        Solo archivos locales; no URLs.
        """
        path = Path(ruta_archivo)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError("Solo se aceptan archivos PDF")

        texto_completo: list[str] = []
        tablas_por_pagina: list[list[list[Optional[str]]]] = []

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                # Texto
                raw = page.extract_text()
                if raw:
                    texto_completo.append(raw)
                # Tablas
                tables = page.extract_tables()
                tablas_por_pagina.append(self._normalize_tables(tables or []))

        return ContenidoPDF(
            texto_completo="\n".join(texto_completo),
            tablas_por_pagina=tablas_por_pagina,
            num_paginas=len(tablas_por_pagina),
        )

    def leer_desde_bytes(self, contenido: bytes) -> ContenidoPDF:
        """Extrae texto y tablas desde bytes (sin escribir en disco)."""
        import io
        buf = io.BytesIO(contenido)
        texto_completo = []
        tablas_por_pagina = []
        with pdfplumber.open(buf) as pdf:
            for page in pdf.pages:
                raw = page.extract_text()
                if raw:
                    texto_completo.append(raw)
                tables = page.extract_tables()
                tablas_por_pagina.append(self._normalize_tables(tables or []))
        return ContenidoPDF(
            texto_completo="\n".join(texto_completo),
            tablas_por_pagina=tablas_por_pagina,
            num_paginas=len(tablas_por_pagina),
        )

    def _normalize_tables(
        self, tables: list[list[list[Optional[str]]]]
    ) -> list[list[list[Optional[str]]]]:
        """Normaliza celdas None a string vacío."""
        out = []
        for table in tables:
            out.append([
                [str(c).strip() if c is not None else "" for c in row]
                for row in table
            ])
        return out
