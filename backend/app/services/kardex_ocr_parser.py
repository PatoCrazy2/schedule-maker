"""
Parser optimizado para kardex BUAP.

Estrategia en 2 rutas (fast-path primero, OCR como fallback):

  RUTA 1 - PDF DIGITAL (texto vectorial via PyMuPDF)
    fitz.get_text("words")  -->  layout analysis  -->  regex  -->  <150ms

  RUTA 2 - PDF ESCANEADO (imagen, sin texto vectorial)
    fitz.get_pixmap()  -->  crop region  -->  split 2 cols
    -->  Tesseract --oem 1 --psm 6 (paralelo)  -->  regex  -->  ~1.5s

Formato de linea esperado:
  NUMERO CLAVE GRUPO CODIGO  NOMBRE_MATERIA  CREDITOS  CALIFICACION
  12304  FGUS  001   107    Formacion Humana y Social  4.00  06

Logica de recursamiento:
  - Extrae (nombre, calificacion) de TODAS las apariciones.
  - Agrupa por nombre normalizado, conserva la calificacion maxima.
  - Filtra calificacion_max >= 6.
"""
from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)
OCR_READY = False
# ─── Config Tesseract ─────────────────────────────────────────────────────────
_TESS_CONFIG = "--oem 1 --psm 6"
_TESS_LANG = "spa"

# ─── Fracciones de recorte (encabezado / pie) ─────────────────────────────────
_HEADER_FRAC = 0.15
_FOOTER_FRAC = 0.05

# ─── Minimo de palabras vectoriales para considerar PDF digital ───────────────
_MIN_WORDS_DIGITAL = 10

# ─── Patrones de linea de materia ─────────────────────────────────────────────
#
# Formato real observado en OCR y texto vectorial:
#   12304FGUS 001 107 Formacion Humana y Social 4.00 06 44836
#   11691 ITIS 005 003 Algebra Lineal con Aplicacione 6.00 07 R1 49951
#   "GUS 002 106 DHPC 4.00 06           <- NRC cortado + basura OCR al inicio
#   ITIS 009 002 Probabilidad y Estadistica 6.00 07 Ri  <- sin NRC (col. derecha)
#   37491 ITIS 009 000 Probabilidad y Estadistica 6.0005 48243  <- espacio OCR perdido

# Patron 1: NRC pegado a clave — "12304FGUS 001 107 Nombre 4.00 06"
_PAT1 = re.compile(
    r"^\s*\d{4,6}[A-Z]{3,6}\s+"
    r"\d{2,3}\s+"
    r"\S+\s+"
    r"(.+?)\s+"
    r"(\d+[.,]\d{2})"
    r"\s*(\d{2})",
    re.IGNORECASE,
)

# Patron 2: NRC separado de clave — "11691 ITIS 005 003 Nombre 6.00 07"
_PAT2 = re.compile(
    r"^\s*\d{4,6}\s+"
    r"[A-Z]{3,6}\s+"
    r"\d{2,3}\s+"
    r"\S+\s+"
    r"(.+?)\s+"
    r"(\d+[.,]\d{2})"
    r"\s*(\d{2})",
    re.IGNORECASE,
)

# Patron 3: sin NRC (columna derecha cortada por split de imagen, o basura OCR al inicio)
# Ej: "GUS 002 106 DHPC 4.00 06"  o  "ITIS 009 002 Nombre 6.00 07 Ri"
_PAT3 = re.compile(
    r"^\s*[A-Z]{3,6}\s+"
    r"\d{2,3}\s+"
    r"\S+\s+"
    r"([A-Z][a-zA-Z\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\s.\-]+?)\s+"
    r"(\d+[.,]\d{2})"
    r"\s*(\d{2})",
    re.IGNORECASE,
)

_PATRONES = (_PAT1, _PAT2, _PAT3)

# ─── Palabras clave a excluir (encabezados / resumen) ────────────────────────
_EXCLUIR_KW = (
    "historia", "promedio", "total", "credito",
    "aprobad", "reprobad", "resumen", "transferencia",
)


# ═══════════════════════════════════════════════════════════════════════════════
# Utilidades comunes
# ═══════════════════════════════════════════════════════════════════════════════

def _limpiar_linea(linea: str) -> str:
    """Elimina ruido OCR al inicio de la linea (comillas, pipes, etc.)."""
    return re.sub(r'^["\'\|#~`]+', '', linea).strip()


def _extraer_entrada(linea: str) -> tuple[str, float] | None:
    """
    Extrae (nombre_materia, calificacion) de una linea sin filtrar por aprobacion.
    Retorna None si la linea no es una fila de materia.
    """
    linea = _limpiar_linea(linea)
    if not linea or len(linea) < 15:
        return None
    for pat in _PATRONES:
        m = pat.search(linea)
        if m:
            nombre = " ".join(m.group(1).split())
            try:
                calif = float(m.group(3).replace(",", "."))
            except ValueError:
                continue
            if len(nombre) >= 4:
                return (nombre, calif)
    return None


def _es_encabezado(nombre: str) -> bool:
    n = nombre.lower()
    return any(kw in n for kw in _EXCLUIR_KW) or len(nombre) < 4


def _agrupar_y_filtrar(entradas: list[tuple[str, float]]) -> list[str]:
    """
    Dado (nombre, calificacion) de TODAS las lineas:
    - Agrupa por nombre normalizado.
    - Conserva la calificacion maxima (maneja recursamiento).
    - Filtra calificacion_max >= 6.
    - Retorna lista ordenada.
    """
    max_calif: dict[str, tuple[str, float]] = {}
    for nombre_raw, calif in entradas:
        nombre = " ".join(nombre_raw.split())
        if _es_encabezado(nombre):
            continue
        key = nombre.lower()
        if key not in max_calif or calif > max_calif[key][1]:
            max_calif[key] = (nombre, calif)

    return sorted(
        nombre for nombre, c in max_calif.values() if c >= 6.0
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RUTA 1 — PDF Digital: layout analysis con PyMuPDF
# ═══════════════════════════════════════════════════════════════════════════════

def _extraer_lineas_vectoriales(pdf_bytes: bytes) -> list[str] | None:
    """
    Usa PyMuPDF para extraer texto vectorial con coordenadas.
    Retorna lista de lineas reconstruidas, o None si el PDF no tiene texto.

    Layout:
      - Ignora 15% superior (encabezado) y 5% inferior (pie).
      - Separa columnas izq/der al 52% del ancho de pagina.
      - Agrupa palabras por fila (threshold Y de 6px).
      - Ordena dentro de cada fila por X.
    """
    try:
        import fitz
    except ImportError:
        return None

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        words = page.get_text("words")  # (x0,y0,x1,y1,word,block,line,wi)
    except Exception as e:
        logger.warning("kardex_ocr_parser: fitz error: %s", e)
        return None

    if not words or len(words) < _MIN_WORDS_DIGITAL:
        return None  # PDF escaneado -> fallback OCR

    pw = page.rect.width
    ph = page.rect.height
    y_min = ph * _HEADER_FRAC
    y_max = ph * (1.0 - _FOOTER_FRAC)
    x_split = pw * 0.52

    # Filtrar region de materias
    cuerpo = [w for w in words if y_min <= w[1] <= y_max]

    # Agrupar por columna (izq/der) y luego por fila (Y aproximado)
    def _agrupar_filas(col_words: list) -> list[str]:
        if not col_words:
            return []
        col_words = sorted(col_words, key=lambda w: (w[1], w[0]))
        filas: list[list] = []
        fila_actual = [col_words[0]]
        y_ref = col_words[0][1]
        for w in col_words[1:]:
            if abs(w[1] - y_ref) <= 6:
                fila_actual.append(w)
            else:
                filas.append(sorted(fila_actual, key=lambda x: x[0]))
                fila_actual = [w]
                y_ref = w[1]
        if fila_actual:
            filas.append(sorted(fila_actual, key=lambda x: x[0]))
        return [" ".join(w[4] for w in fila) for fila in filas]

    izq = [w for w in cuerpo if w[0] < x_split]
    der = [w for w in cuerpo if w[0] >= x_split]

    lineas = _agrupar_filas(izq) + _agrupar_filas(der)
    logger.debug("kardex_ocr_parser: %d palabras vectoriales -> %d lineas", len(words), len(lineas))
    return lineas


# ═══════════════════════════════════════════════════════════════════════════════
# RUTA 2 — PDF Escaneado: OCR con PyMuPDF + Tesseract
# ═══════════════════════════════════════════════════════════════════════════════

def _configurar_tesseract() -> bool:
    """Auto-configura pytesseract para Windows (UB-Mannheim installer) y tessdata usuario."""
    import os
    import shutil
    try:
        import pytesseract
    except ImportError:
        return False

    if not shutil.which("tesseract"):
        win_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.isfile(win_default):
            pytesseract.pytesseract.tesseract_cmd = win_default
        else:
            return False

    user_tessdata = os.path.join(os.path.expanduser("~"), ".tessdata")
    if os.path.isdir(user_tessdata):
        os.environ.setdefault("TESSDATA_PREFIX", user_tessdata)

    tessdata_dir = os.environ.get("TESSDATA_PREFIX",
                                  r"C:\Program Files\Tesseract-OCR\tessdata")
    global _TESS_LANG
    if not os.path.isfile(os.path.join(tessdata_dir, "spa.traineddata")):
        _TESS_LANG = "eng"
        logger.info("kardex_ocr_parser: spa.traineddata no encontrado, usando eng")

    return True


def _ocr_disponible() -> bool:
    global OCR_READY

    if OCR_READY:
        return True

    try:
        import pytesseract
        _configurar_tesseract()
        pytesseract.get_tesseract_version()
        OCR_READY = True
        return True
    except Exception as e:
        logger.warning("Tesseract no disponible: %s", e)
        return False


def _ocr_pil(img_pil) -> str:
    import pytesseract
    try:
        return pytesseract.image_to_string(img_pil, lang=_TESS_LANG, config=_TESS_CONFIG) or ""
    except Exception as e:
        logger.warning("kardex_ocr_parser: error OCR region: %s", e)
        return ""


def _extraer_lineas_ocr(pdf_bytes: bytes) -> list[str]:
    """
    Ruta OCR: PyMuPDF renderiza la pagina como imagen (sin poppler),
    recorta la region de materias, divide en 2 columnas, OCR en paralelo.
    """
    try:
        import fitz
        from PIL import Image
        import io
    except ImportError as e:
        logger.error("kardex_ocr_parser: dependencias OCR no disponibles: %s", e)
        return []

    if not _ocr_disponible():
        return []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        # Renderizar a 200 DPI: mat = zoom * identity (72 DPI base de fitz)
        zoom = 200 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        logger.warning("kardex_ocr_parser: error renderizando PDF: %s", e)
        return []

    w, h = img.size
    top = int(h * _HEADER_FRAC)
    bottom = int(h * (1.0 - _FOOTER_FRAC))
    body = img.crop((0, top, w, bottom))
    bw, bh = body.size

    col_izq = body.crop((0, 0, bw // 2, bh))
    col_der = body.crop((bw // 2, 0, bw, bh))

    textos: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_ocr_pil, col_izq), pool.submit(_ocr_pil, col_der)]
        for fut in futures:
            txt = fut.result()
            if txt:
                textos.append(txt)

    lineas: list[str] = []
    for texto in textos:
        lineas.extend(texto.splitlines())
    return lineas


# ═══════════════════════════════════════════════════════════════════════════════
# API publica
# ═══════════════════════════════════════════════════════════════════════════════

def parsear_kardex_ocr(pdf_bytes: bytes) -> list[str]:

    entradas: list[tuple[str, float]] = []

    # ─────────────────────
    # Ruta vectorial
    # ─────────────────────

    lineas = _extraer_lineas_vectoriales(pdf_bytes)

    if lineas and len(lineas) > 10:
        for linea in lineas:
            entrada = _extraer_entrada(linea)
            if entrada:
                entradas.append(entrada)

        resultado = _agrupar_y_filtrar(entradas)

        logger.info(
            "kardex_parser [vectorial]: %d entradas -> %d aprobadas",
            len(entradas),
            len(resultado),
        )

        return resultado

    # ─────────────────────
    # OCR fallback
    # ─────────────────────

    logger.info("kardex_parser: fallback OCR")

    lineas = _extraer_lineas_ocr(pdf_bytes)

    for linea in lineas:
        entrada = _extraer_entrada(linea)
        if entrada:
            entradas.append(entrada)

    resultado = _agrupar_y_filtrar(entradas)

    logger.info(
        "kardex_parser [OCR]: %d entradas -> %d aprobadas",
        len(entradas),
        len(resultado),
    )

    return resultado
