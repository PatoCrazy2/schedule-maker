"""
Parser para PDF de mapa curricular BUAP (malla curricular).

Dos modos:
- Con layout (geometria): columnas por X = semestres, bloques por Y; validacion estructural.
- Sin layout (fallback): texto plano + regex + validacion fuerte.

Leyenda en cada bloque: H Teoria, H Lab, H Trabajo indep., Creditos.
"""
import re
from typing import TYPE_CHECKING

from app.models.schemas import MateriaPlan
from app.services.lector_pdf import ContenidoPDF
from app.services.parsers.base_parser import BaseOfertaParser

if TYPE_CHECKING:
    from app.services.layout_ocr import BloqueColumna

# Encabezados que no son nombres de materia (descarte estructural)
ENCABEZADOS_MAPA = frozenset({
    "PERIODO", "PERIODOS", "SEMESTRE", "SEMESTRES", "NIVEL", "AREA", "CREDITOS",
    "HORAS", "TEORIA", "LABORATORIO", "TRABAJO", "INDEPENDIENTE", "MALLA", "PLAN",
    "DHPC",
})

# Si el nombre contiene alguna de estas cadenas, se descarta (encabezados/etiquetas)
DESCARTAR_SI_CONTIENE = ("PERIODO", "SEMESTRE", "1 2 3 4", "2 3 4 5", "CREDITOS", "HORAS DE")


def _es_encabezado(s: str) -> bool:
    """True si el texto parece un encabezado, no nombre de materia."""
    t = (s or "").strip().upper()
    if not t or len(t) < 3:
        return True
    if t in ENCABEZADOS_MAPA:
        return True
    for frag in DESCARTAR_SI_CONTIENE:
        if frag in t:
            return True
    if re.match(r"^PERIODO\s*[\d\s,]*$", t) or re.match(r"^SEMESTRE\s*[\d\s]*$", t):
        return True
    if re.match(r"^\d[\d\s,]*$", t):
        return True
    if re.match(r"^[A-Z]\s*\d{2,3}\s*\d$", t):
        return True
    return False


def _valores_razonables(h: int, lab: int, ti: int, c: int) -> bool:
    """True si los numeros parecen H/L/TI/Creditos (no una linea de encabezado)."""
    if not (0 <= c <= 20):
        return False
    if not (0 <= h <= 8 and 0 <= lab <= 8 and 0 <= ti <= 10):
        return False
    return True


class MapaCurricularParser(BaseOfertaParser):
    """Extrae materias del plan desde un PDF de mapa curricular."""

    def puede_parsear(self, contenido: ContenidoPDF, nombre_archivo: str = "") -> bool:
        texto = (contenido.texto_completo or "").upper()
        if "MAPA" in nombre_archivo.upper() or "CARRERA" in nombre_archivo.upper() or "CURRICULAR" in nombre_archivo.upper():
            return True
        if re.search(r"CRÉDITOS|CREDITOS|PERIODO|MALLA|PLAN\s+DE\s+ESTUDIOS", texto):
            return True
        return True

    def extraer_filas(self, contenido: ContenidoPDF, nombre_archivo: str = ""):
        return []

    def extraer_materias(self, contenido: ContenidoPDF, nombre_archivo: str = ""):
        return []

    def extraer_materias_plan(self, contenido: ContenidoPDF, nombre_archivo: str = "") -> list[MateriaPlan]:
        """
        Extrae MateriaPlan: nombre + 4 numeros (Teoria, Lab, Trabajo indep., Creditos).
        Acepta "nombre 3 2 0 6" o "nombre 320 6" (OCR junta 3 2 0).
        """
        materias: list[MateriaPlan] = []
        texto = contenido.texto_completo or ""
        vistos: set[str] = set()

        for line in texto.splitlines():
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # Formato 1: nombre + cuatro numeros separados "N N N N" (H L TI C)
            m1 = re.match(r"^(.+?)\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s*$", line)
            if m1:
                nombre_part, h, lab, ti, c = m1.groups()
                horas_teoria, horas_lab, horas_ti, creditos = int(h), int(lab), int(ti), int(c)
                if not _valores_razonables(horas_teoria, horas_lab, horas_ti, creditos):
                    continue
                nombre_limpio = _limpiar_nombre_materia(nombre_part)
                if not nombre_limpio or len(nombre_limpio) < 2 or _es_encabezado(nombre_limpio):
                    continue
                clave = _nombre_a_clave(nombre_limpio)
                if clave not in vistos:
                    vistos.add(clave)
                    materias.append(
                        MateriaPlan(
                            clave=clave,
                            nombre=nombre_limpio,
                            creditos=creditos,
                            horas_teoria=horas_teoria,
                            horas_lab=horas_lab,
                            horas_trabajo_indep=horas_ti,
                            periodo=None,
                            area=None,
                        )
                    )
                continue

            # Formato 2: OCR junta "3 2 0" en "320" -> "nombre 320 6" (creditos al final)
            m2 = re.match(r"^(.+?)\s+(\d)(\d)(\d)\s+(\d{1,2})\s*$", line)
            if m2:
                nombre_part, d1, d2, d3, cred = m2.groups()
                horas_teoria, horas_lab, horas_ti = int(d1), int(d2), int(d3)
                creditos = int(cred)
                if not _valores_razonables(horas_teoria, horas_lab, horas_ti, creditos):
                    continue
                nombre_limpio = _limpiar_nombre_materia(nombre_part)
                if not nombre_limpio or len(nombre_limpio) < 2 or _es_encabezado(nombre_limpio):
                    continue
                clave = _nombre_a_clave(nombre_limpio)
                if clave not in vistos:
                    vistos.add(clave)
                    materias.append(
                        MateriaPlan(
                            clave=clave,
                            nombre=nombre_limpio,
                            creditos=creditos,
                            horas_teoria=horas_teoria,
                            horas_lab=horas_lab,
                            horas_trabajo_indep=horas_ti,
                            periodo=None,
                            area=None,
                        )
                    )
                continue

        return materias


def _limpiar_nombre_materia(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    if re.match(r"^\d+\s*$", s):
        return ""
    return s


def _nombre_a_clave(nombre: str) -> str:
    """Clave de display para el mapa; cruce con oferta por nombre o clave de la oferta."""
    return (nombre or "").strip()[:80]


def extraer_materias_plan_desde_layout(layout: list["BloqueColumna"]) -> list[MateriaPlan]:
    """
    Parsea bloques obtenidos por layout OCR (columnas = semestres, lineas por bloque).
    Validacion estructural: solo lineas que tienen nombre + 4 numeros (H L TI C).
    """
    materias: list[MateriaPlan] = []
    vistos: set[str] = set()
    for bloque in layout:
        periodo = bloque.periodo
        for line in bloque.lineas:
            line = (line or "").strip()
            if not line or len(line) < 5:
                continue
            if any(frag in line.upper() for frag in DESCARTAR_SI_CONTIENE):
                continue
            m1 = re.match(r"^(.+?)\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s*$", line)
            if m1:
                nombre_part, h, lab, ti, c = m1.groups()
                horas_teoria, horas_lab, horas_ti, creditos = int(h), int(lab), int(ti), int(c)
                if not _valores_razonables(horas_teoria, horas_lab, horas_ti, creditos):
                    continue
                nombre_limpio = _limpiar_nombre_materia(nombre_part)
                if not nombre_limpio or len(nombre_limpio) < 4 or _es_encabezado(nombre_limpio):
                    continue
                clave = _nombre_a_clave(nombre_limpio)
                if clave not in vistos:
                    vistos.add(clave)
                    materias.append(
                        MateriaPlan(
                            clave=clave,
                            nombre=nombre_limpio,
                            creditos=creditos,
                            horas_teoria=horas_teoria,
                            horas_lab=horas_lab,
                            horas_trabajo_indep=horas_ti,
                            periodo=periodo,
                            area=None,
                        )
                    )
                continue
            m2 = re.match(r"^(.+?)\s+(\d)(\d)(\d)\s+(\d{1,2})\s*$", line)
            if m2:
                nombre_part, d1, d2, d3, cred = m2.groups()
                horas_teoria, horas_lab, horas_ti = int(d1), int(d2), int(d3)
                creditos = int(cred)
                if not _valores_razonables(horas_teoria, horas_lab, horas_ti, creditos):
                    continue
                nombre_limpio = _limpiar_nombre_materia(nombre_part)
                if not nombre_limpio or len(nombre_limpio) < 4 or _es_encabezado(nombre_limpio):
                    continue
                clave = _nombre_a_clave(nombre_limpio)
                if clave not in vistos:
                    vistos.add(clave)
                    materias.append(
                        MateriaPlan(
                            clave=clave,
                            nombre=nombre_limpio,
                            creditos=creditos,
                            horas_teoria=horas_teoria,
                            horas_lab=horas_lab,
                            horas_trabajo_indep=horas_ti,
                            periodo=periodo,
                            area=None,
                        )
                    )
    return materias
