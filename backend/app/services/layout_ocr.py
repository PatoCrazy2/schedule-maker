"""
Motor de interpretación estructural para mapas curriculares (PDF-imagen).

Pipeline: PDF -> imagen -> OCR con bounding boxes -> columnas por X (semestres)
-> agrupación por bloques (Y) -> validación semántica.

No regex sobre texto plano: se usa geometría (columnas, proximidad vertical).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PalabraBox:
    """Palabra con caja (coordenadas)."""
    text: str
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def center_x(self) -> int:
        return self.left + self.width // 2

    @property
    def center_y(self) -> int:
        return self.top + self.height // 2


@dataclass
class BloqueColumna:
    """Bloque de texto en una columna (semestre): líneas agrupadas por proximidad Y."""
    periodo: int
    lineas: list[str] = field(default_factory=list)


def _ocr_disponible() -> bool:
    from app.services.ocr_pdf import ocr_disponible
    return ocr_disponible()


def extraer_layout_desde_bytes(
    contenido_pdf: bytes,
    num_columnas: int = 9,
    dpi: int = 300,
    idioma: str = "spa",
) -> list[BloqueColumna]:
    """
    Convierte PDF a imagen, OCR con cajas, asigna palabras a columnas por X,
    agrupa por proximidad Y en bloques. Devuelve lista de bloques por columna (periodo).
    """
    if not _ocr_disponible():
        return []
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        from pytesseract import Output
    except ImportError:
        return []

    try:
        images = convert_from_bytes(contenido_pdf, dpi=dpi)
    except Exception as e:
        logger.warning("layout_ocr: error convirtiendo PDF a imagen: %s", e)
        return []

    if not images:
        logger.warning("layout_ocr: PDF no produjo imagenes")
        return []

    todos_bloques: list[BloqueColumna] = []
    for num_pagina, img in enumerate(images):
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        try:
            data = pytesseract.image_to_data(img, lang=idioma, output_type=Output.DICT)
        except Exception as e:
            logger.warning("layout_ocr: error image_to_data pagina %s: %s", num_pagina + 1, e)
            continue

        palabras: list[PalabraBox] = []
        texts = data.get("text", [])
        n = len(texts)
        for i in range(n):
            text = (texts[i] or "").strip()
            if not text:
                continue
            left = int(data.get("left", [0])[i])
            top = int(data.get("top", [0])[i])
            width = int(data.get("width", [0])[i])
            height = int(data.get("height", [0])[i])
            palabras.append(PalabraBox(text=text, left=left, top=top, width=width, height=height))

        if not palabras:
            logger.warning(
                "layout_ocr: pagina %s sin palabras (image_to_data devolvio %s entradas)",
                num_pagina + 1, n,
            )
            continue

        # Asignar cada palabra a columna por X (semestre 1..num_columnas)
        col_width = max(1, w // num_columnas)
        columnas: dict[int, list[PalabraBox]] = {i: [] for i in range(num_columnas)}
        for p in palabras:
            col = min(int(p.center_x / col_width), num_columnas - 1)
            columnas[col].append(p)

        # Dentro de cada columna: ordenar por Y y agrupar en líneas (misma Y aprox), luego en bloques
        for col_idx in range(num_columnas):
            pals = columnas[col_idx]
            if not pals:
                continue
            pals.sort(key=lambda x: (x.top, x.left))
            lineas = _agrupar_en_lineas(pals)
            bloques = _agrupar_lineas_en_bloques(lineas)
            for bloque in bloques:
                todos_bloques.append(BloqueColumna(periodo=col_idx + 1, lineas=bloque))
    if not todos_bloques:
        logger.warning(
            "layout_ocr: 0 bloques (imagenes=%s). Revisar DPI, idioma o diseno del PDF.",
            len(images),
        )
    else:
        logger.info("layout_ocr: %s paginas, %s bloques totales", len(images), len(todos_bloques))
    return todos_bloques


def _agrupar_en_lineas(palabras: list[PalabraBox], umbral_y: int = 15) -> list[list[PalabraBox]]:
    """Agrupa palabras en la misma línea (diferencia de Y menor que umbral_y)."""
    if not palabras:
        return []
    lineas: list[list[PalabraBox]] = []
    linea_actual: list[PalabraBox] = [palabras[0]]
    y_ref = palabras[0].center_y
    for p in palabras[1:]:
        if abs(p.center_y - y_ref) <= umbral_y:
            linea_actual.append(p)
        else:
            linea_actual.sort(key=lambda x: x.left)
            lineas.append(linea_actual)
            linea_actual = [p]
            y_ref = p.center_y
    if linea_actual:
        linea_actual.sort(key=lambda x: x.left)
        lineas.append(linea_actual)
    return lineas


def _agrupar_lineas_en_bloques(
    lineas: list[list[PalabraBox]],
    umbral_gap_y: int = 25,
) -> list[list[str]]:
    """
    Agrupa líneas en bloques cuando el salto vertical es mayor que umbral_gap_y.
    Cada bloque es una lista de strings (una por línea).
    """
    if not lineas:
        return []
    bloques: list[list[str]] = []
    bloque_actual: list[str] = [" ".join(p.text for p in lineas[0])]
    y_anterior = lineas[0][-1].bottom if lineas[0] else 0
    for li in lineas[1:]:
        y_actual = li[0].top if li else 0
        if li and (y_actual - y_anterior) > umbral_gap_y and bloque_actual:
            bloques.append(bloque_actual)
            bloque_actual = []
        bloque_actual.append(" ".join(p.text for p in li))
        if li:
            y_anterior = li[-1].bottom
    if bloque_actual:
        bloques.append(bloque_actual)
    return bloques


def layout_a_texto_por_periodo(layout: list[BloqueColumna]) -> str:
    """Convierte layout a texto plano con marcas de periodo (para parser actual si hace falta fallback)."""
    partes = []
    for b in layout:
        partes.append(f"[PERIODO {b.periodo}]")
        for linea in b.lineas:
            partes.append(linea)
    return "\n".join(partes)
