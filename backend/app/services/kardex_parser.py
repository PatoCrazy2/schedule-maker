"""
Parser de kardex BUAP (autoservicios).

Extrae unicamente los nombres de materias aprobadas o en curso.
No se guardan datos personales, matriculas ni calificaciones.
"""
import re

from app.services.lector_pdf import ContenidoPDF, LectorPDF


def _normalizar_nombre(nombre: str) -> str:
    """Limpia y normaliza el nombre para comparacion."""
    return (nombre or "").strip()


def _extraer_desde_texto(texto: str) -> set[str]:
    """
    Extrae nombres de materias desde texto plano (extraccion PDF).
    Formato BUAP: NRC CLAVE SECC NOMBRE CREDITOS [CALIF]
    Ej: 12304 FGUS 001 107 Formacion Humana y Social 4.00 07
    """
    nombres: set[str] = set()
    lineas = (texto or "").splitlines()

    # Patron BUAP: NRC(5dig) [sin espacio] CLAVE(XXX XXX) SECC(3dig) NOMBRE X.XX
    # Ej: 12304 FGUS 001 107 Formacion Humana y Social 4.00
    # Ej: 26086CCOS 260 002 Redes de Computadoras 6.00
    patron = re.compile(
        r"\d{5}\s*[A-Z0-9]{4}\s+\d{2,3}\s+\d{3}\s+(.+?)\s+\d+\.\d{2}",
        re.IGNORECASE,
    )

    for linea in lineas:
        linea = linea.strip()
        if len(linea) < 20:
            continue
        m = patron.search(linea)
        if m:
            nombre = _normalizar_nombre(m.group(1))
            if nombre and len(nombre) >= 3:
                nombres.add(nombre)

    return nombres


def _extraer_desde_tablas(tablas_por_pagina: list) -> set[str]:
    """
    Extrae nombres desde tablas (pdfplumber).
    Busca columnas con texto que parezca nombre de materia (no solo numeros).
    """
    nombres: set[str] = set()

    for pag in tablas_por_pagina or []:
        for tabla in pag or []:
            if not tabla or len(tabla) < 2:
                continue
            header = [str(c).strip().lower() for c in (tabla[0] if tabla else [])]
            col_nombre = None
            for i, h in enumerate(header):
                if h and ("materia" in h or "asignatura" in h or "nombre" in h):
                    col_nombre = i
                    break
            if col_nombre is None:
                # Heuristica: columna con texto mas largo que no sea solo numeros
                for row in tabla[1:]:
                    for j, cell in enumerate(row or []):
                        val = str(cell or "").strip()
                        if len(val) > 10 and not re.match(r"^[\d.\s]+$", val):
                            if not val.isdigit() and "Aprobadas" not in val:
                                nombres.add(val)
                continue
            for row in tabla[1:]:
                if row and len(row) > col_nombre:
                    val = str(row[col_nombre] or "").strip()
                    if val and len(val) >= 3 and not re.match(r"^[\d.\s]+$", val):
                        nombres.add(val)

    return nombres


def extraer_materias_aprobadas(contenido: ContenidoPDF) -> list[str]:
    """
    Extrae solo los nombres de materias (aprobadas o en curso) del kardex.
    Sin datos personales. Retorna lista ordenada sin duplicados.
    """
    desde_texto = _extraer_desde_texto(contenido.texto_completo or "")
    desde_tablas = _extraer_desde_tablas(contenido.tablas_por_pagina or [])

    todos = desde_texto | desde_tablas

    # Excluir lineas que son encabezados o resumenes
    excluir = {
        "aprobadas",
        "reprobadas",
        "cred",
        "puntos",
        "prom",
        "resumen",
        "total",
        "creditos",
        "transferencias",
        "institucion",
        "minimos",
        "maximos",
        "carga en progreso",
        "historia academica",
        "promedio aritmetico",
    }
    resultado = []
    for n in sorted(todos):
        n_lower = n.lower()
        if any(ex in n_lower for ex in excluir):
            continue
        if len(n) < 4:
            continue
        resultado.append(n)

    return resultado


def parsear_kardex_desde_bytes(contenido_bytes: bytes) -> list[str]:
    """Parsea kardex desde bytes (upload)."""
    lector = LectorPDF()
    contenido = lector.leer_desde_bytes(contenido_bytes)
    return extraer_materias_aprobadas(contenido)
