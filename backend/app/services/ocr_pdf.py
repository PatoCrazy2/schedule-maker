"""
OCR para PDF que son solo imagen: extrae texto con Tesseract (español).

Requiere: tesseract-ocr, tesseract-ocr-spa, poppler-utils (sistema)
y en Python: pdf2image, pytesseract.
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_OCR_DISPONIBLE: Optional[bool] = None


def ocr_disponible() -> bool:
    """True si Tesseract y pdf2image están instalados y funcionan."""
    global _OCR_DISPONIBLE
    if _OCR_DISPONIBLE is not None:
        return _OCR_DISPONIBLE
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        # Comprobar que tesseract responde
        pytesseract.get_tesseract_version()
        _OCR_DISPONIBLE = True
    except Exception as e:
        logger.warning("OCR no disponible: %s", e)
        _OCR_DISPONIBLE = False
    return _OCR_DISPONIBLE


def extraer_texto_desde_bytes(
    contenido_pdf: bytes,
    idioma: str = "spa",
    dpi: int = 200,
) -> str:
    """
    Convierte cada página del PDF a imagen y extrae texto con Tesseract (OCR).

    Args:
        contenido_pdf: bytes del PDF.
        idioma: código de idioma para Tesseract (spa = español).
        dpi: resolución para la conversión PDF -> imagen (más alto = más lento, más preciso).

    Returns:
        Texto extraído de todas las páginas concatenado.
    """
    if not ocr_disponible():
        return ""
    import pytesseract
    from pdf2image import convert_from_bytes
    try:
        images = convert_from_bytes(contenido_pdf, dpi=dpi)
        textos = []
        for i, img in enumerate(images):
            try:
                text = pytesseract.image_to_string(img, lang=idioma)
                if text and text.strip():
                    textos.append(text.strip())
            except Exception as e:
                logger.warning("Error OCR en página %s: %s", i + 1, e)
        return "\n\n".join(textos) if textos else ""
    except Exception as e:
        logger.warning("Error en OCR del PDF: %s", e)
        return ""


def extraer_texto_desde_ruta(
    ruta: Path | str,
    idioma: str = "spa",
    dpi: int = 200,
) -> str:
    """Extrae texto por OCR desde un PDF en disco."""
    path = Path(ruta)
    if not path.exists():
        return ""
    contenido = path.read_bytes()
    return extraer_texto_desde_bytes(contenido, idioma=idioma, dpi=dpi)
