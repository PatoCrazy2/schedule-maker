"""
Parser de mapa curricular: intenta primero interpretacion estructural (layout),
luego fallback a OCR plano + regex. Si hay layout con bloques, asigna periodo a las materias del fallback.
"""
import logging
from pathlib import Path

from app.models.schemas import MapaCurricularExtraido, MateriaPlan
from app.services.layout_ocr import BloqueColumna, extraer_layout_desde_bytes
from app.services.lector_pdf import LectorPDF, ContenidoPDF
from app.services.ocr_pdf import extraer_texto_desde_bytes, extraer_texto_desde_ruta, ocr_disponible
from app.services.parsers.mapa_parser import MapaCurricularParser, extraer_materias_plan_desde_layout

logger = logging.getLogger(__name__)


def _asignar_periodo_desde_layout(
    resultado: MapaCurricularExtraido,
    layout: list[BloqueColumna],
) -> MapaCurricularExtraido:
    """
    Asigna periodo a cada materia buscando en que bloque del layout aparece su nombre o clave.
    """
    def _normalizar(s: str) -> str:
        return (s or "").strip().upper().replace(" ", "")

    out: list[MateriaPlan] = []
    for m in resultado.materias:
        periodo_asignado: int | None = None
        clave_n = _normalizar(m.clave)
        nombre_n = _normalizar(m.nombre)
        for bloque in layout:
            for linea in bloque.lineas:
                linea_n = _normalizar(linea)
                if clave_n and clave_n in linea_n:
                    periodo_asignado = bloque.periodo
                    break
                if nombre_n and len(nombre_n) >= 3 and nombre_n in linea_n:
                    periodo_asignado = bloque.periodo
                    break
            if periodo_asignado is not None:
                break
        out.append(
            MateriaPlan(
                clave=m.clave,
                nombre=m.nombre,
                creditos=m.creditos,
                horas_teoria=m.horas_teoria,
                horas_lab=m.horas_lab,
                horas_trabajo_indep=m.horas_trabajo_indep,
                periodo=periodo_asignado or m.periodo,
                area=m.area,
            )
        )
    return MapaCurricularExtraido(
        materias=out,
        archivos_procesados=resultado.archivos_procesados,
        advertencia=resultado.advertencia,
    )


class ParserMapaCurricular:
    """Lee un PDF de mapa curricular y extrae MateriaPlan (clave, nombre, creditos, periodo)."""

    def __init__(self) -> None:
        self.lector = LectorPDF()
        self.parser = MapaCurricularParser()

    def parsear_desde_ruta(self, file_path: Path) -> MapaCurricularExtraido:
        contenido = self.lector.leer(file_path)
        texto = (contenido.texto_completo or "").strip()
        if texto and len(texto) >= 50:
            return self._parsear(contenido, file_path.name)
        bytes_pdf = file_path.read_bytes()
        layout = extraer_layout_desde_bytes(bytes_pdf)
        if layout:
            materias = extraer_materias_plan_desde_layout(layout)
            if materias:
                return MapaCurricularExtraido(
                    materias=materias,
                    archivos_procesados=[file_path.name],
                )
        contenido = self._aplicar_ocr_si_falta_texto_ruta(contenido, file_path)
        return self._parsear(contenido, file_path.name)

    def parsear_desde_bytes(self, contenido_bytes: bytes, nombre_archivo: str = "mapa.pdf") -> MapaCurricularExtraido:
        contenido = self.lector.leer_desde_bytes(contenido_bytes)
        # Siempre intentar layout primero (geometria) para poder asignar periodo; si hay texto se usara en fallback.
        layout = extraer_layout_desde_bytes(contenido_bytes)
        if layout:
            materias_layout = extraer_materias_plan_desde_layout(layout)
            if materias_layout:
                logger.info("Mapa parseado por layout: %s materias", len(materias_layout))
                return MapaCurricularExtraido(
                    materias=materias_layout,
                    archivos_procesados=[nombre_archivo],
                )
        contenido = self._aplicar_ocr_si_falta_texto_bytes(contenido, contenido_bytes)
        resultado = self._parsear(contenido, nombre_archivo)
        if layout and resultado.materias:
            resultado = _asignar_periodo_desde_layout(resultado, layout)
        return resultado

    def _aplicar_ocr_si_falta_texto_ruta(self, contenido: ContenidoPDF, path: Path) -> ContenidoPDF:
        texto = (contenido.texto_completo or "").strip()
        if len(texto) >= 50 or not ocr_disponible():
            return contenido
        logger.info("Poco texto en PDF, aplicando OCR (ruta) para %s", path.name)
        texto_ocr = extraer_texto_desde_ruta(path)
        if not texto_ocr or len(texto_ocr.strip()) < 20:
            return contenido
        return ContenidoPDF(
            texto_completo=texto_ocr,
            tablas_por_pagina=[[] for _ in range(contenido.num_paginas)],
            num_paginas=contenido.num_paginas,
        )

    def _aplicar_ocr_si_falta_texto_bytes(self, contenido: ContenidoPDF, contenido_bytes: bytes) -> ContenidoPDF:
        texto = (contenido.texto_completo or "").strip()
        if len(texto) >= 50 or not ocr_disponible():
            return contenido
        logger.info("Poco texto en PDF, aplicando OCR (bytes)")
        texto_ocr = extraer_texto_desde_bytes(contenido_bytes)
        if not texto_ocr or len(texto_ocr.strip()) < 20:
            return contenido
        return ContenidoPDF(
            texto_completo=texto_ocr,
            tablas_por_pagina=[[] for _ in range(contenido.num_paginas)],
            num_paginas=contenido.num_paginas,
        )

    def _parsear(self, contenido: ContenidoPDF, nombre_archivo: str) -> MapaCurricularExtraido:
        texto = (contenido.texto_completo or "").strip()
        if len(texto) < 50:
            advertencia = (
                "El PDF tiene poco o ningun texto extraíble (p. ej. es solo imagen). "
                "Se necesita texto para extraer materias."
            )
            if not ocr_disponible():
                advertencia += " OCR no esta disponible (instale tesseract-ocr y tesseract-ocr-spa)."
            else:
                advertencia += " El OCR no logro extraer suficiente texto."
            return MapaCurricularExtraido(
                materias=[],
                archivos_procesados=[nombre_archivo],
                advertencia=advertencia,
            )
        if not self.parser.puede_parsear(contenido, nombre_archivo):
            logger.warning("El parser de mapa no reconoce %s", nombre_archivo)
            return MapaCurricularExtraido(archivos_procesados=[nombre_archivo])
        materias = self.parser.extraer_materias_plan(contenido, nombre_archivo)
        return MapaCurricularExtraido(
            materias=materias,
            archivos_procesados=[nombre_archivo],
        )
