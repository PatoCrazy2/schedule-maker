"""
Parser para PDF de horario del alumno (schedule de cursos inscritos).
Formato BUAP: tabla con CODIGO, SEC, MATERIAS, LUNES, MARTES, ... y filas extra para salon, NRC, profesor.
"""
import re
import logging
from typing import Optional

from app.models.schemas import HorarioSlot, MateriaExtraida
from app.services.lector_pdf import LectorPDF, ContenidoPDF

logger = logging.getLogger(__name__)

DIAS_COLUMNAS = ["LUNES", "MARTES", "MIERCOLES", "MIÉRCOLES", "JUEVES", "VIERNES", "SABADO", "SÁBADO", "DOMINGO"]
DIAS_CODIGO: dict[str, str] = {
    "LUNES": "L", "MARTES": "A", "MIERCOLES": "M", "MIÉRCOLES": "M",
    "JUEVES": "J", "VIERNES": "V", "SABADO": "S", "SÁBADO": "S", "DOMINGO": "D",
}

CODIGO_PATTERN = re.compile(r"^([A-Z]{2,6}[-\s]?\d{2,3})\s*$", re.I)
HORA_PATTERN = re.compile(r"(\d{1,2}):?(\d{2})-(\d{1,2}):?(\d{2})|(\d{4})-(\d{4})")
HORA_PATTERN_FLEX = re.compile(r"(\d{4})-(\d{2,4})?")
NRC_PATTERN = re.compile(r"^\d{5}$")
SALON_PATTERN = re.compile(r"^[\dA-Z]+[\s/]\d+$", re.I)


def _normalizar_hora(s: str) -> str:
    s = (s or "").strip()
    if len(s) == 4 and s.isdigit():
        return f"{s[:2]}:{s[2:]}"
    return s


def _parse_hora(celda: str) -> tuple[str, str] | None:
    m = HORA_PATTERN.search(celda or "")
    if m:
        if m.group(1) is not None:
            return (f"{m.group(1).zfill(2)}:{m.group(2)}", f"{m.group(3).zfill(2)}:{m.group(4)}")
        return (_normalizar_hora(m.group(5)), _normalizar_hora(m.group(6)))
    m2 = HORA_PATTERN_FLEX.search(celda or "")
    if m2:
        hi = _normalizar_hora(m2.group(1))
        hf_raw = m2.group(2)
        if hf_raw and len(hf_raw) >= 2:
            hf = _normalizar_hora(hf_raw)
        else:
            h0, m0 = int(m2.group(1)[:2]), int(m2.group(1)[2:]) if len(m2.group(1)) >= 4 else 0
            m0 = m0 + 59
            if m0 >= 60:
                m0 -= 60
                h0 += 1
            hf = f"{h0:02d}:{m0:02d}"
        return (hi, hf)
    return None


def _extraer_desde_tablas(contenido: ContenidoPDF) -> list[MateriaExtraida]:
    """Parsea tablas del PDF. Busca estructura CODIGO SEC MATERIAS | LUNES | MARTES | ..."""
    materias: list[MateriaExtraida] = []
    indices_dias: dict[int, str] = {}  # col_idx -> codigo dia

    for tablas in contenido.tablas_por_pagina:
        for table in tablas:
            if not table or len(table) < 2:
                continue

            for row_idx, row in enumerate(table):
                cells = [str(c or "").strip() for c in row]
                if not cells:
                    continue

                primera = cells[0].upper()

                if not indices_dias and any(d in primera for d in DIAS_COLUMNAS):
                    for i, c in enumerate(cells):
                        for d in DIAS_COLUMNAS:
                            if d in (c or "").upper():
                                indices_dias[i] = DIAS_CODIGO.get(d, d[0])
                                break

                if CODIGO_PATTERN.match(primera) and len(cells) >= 2:
                    codigo = primera.replace(" ", "-")
                    seccion = cells[1].strip() or "-"
                    materia_nombre = cells[2] if len(cells) > 2 else codigo

                    for token in (cells[2], cells[3]) if len(cells) > 3 else []:
                        if token and len(token) > 4 and not HORA_PATTERN.search(token):
                            if token != seccion and not NRC_PATTERN.match(token):
                                materia_nombre = token
                                break

                    horarios: list[HorarioSlot] = []
                    for col_idx, cod_dia in indices_dias.items():
                        if col_idx < len(cells):
                            val = cells[col_idx]
                            if val and val != "-":
                                par = _parse_hora(val)
                                if par:
                                    horarios.append(HorarioSlot(
                                        dia=cod_dia,
                                        hora_inicio=par[0],
                                        hora_fin=par[1],
                                        aula=None,
                                    ))

                    nrc: Optional[str] = None
                    salon: Optional[str] = None
                    profesor: Optional[str] = None

                    for j in range(row_idx + 1, min(row_idx + 4, len(table))):
                        sig_row = [str(c or "").strip() for c in table[j]]
                        for c in sig_row:
                            if NRC_PATTERN.match(c):
                                nrc = c
                            elif SALON_PATTERN.match(c) or re.match(r"^\dCCO\d+\s*\d+", c, re.I):
                                salon = c
                            elif re.match(r"^[A-ZÁÉÍÓÚÑ][A-Za-z\s\-]+$", c) and len(c) > 6:
                                profesor = c

                    if horarios or materia_nombre:
                        slots = [
                            HorarioSlot(
                                dia=h.dia,
                                hora_inicio=h.hora_inicio,
                                hora_fin=h.hora_fin,
                                aula=salon or h.aula,
                            )
                            for h in horarios
                        ]
                        materias.append(MateriaExtraida(
                            clave=codigo,
                            grupo=seccion,
                            nombre=materia_nombre or codigo,
                            nrc=nrc,
                            profesor=profesor,
                            horarios=slots,
                        ))

    return materias


def _extraer_desde_texto(texto: str) -> list[MateriaExtraida]:
    """Fallback: parsea texto plano. Soporta codigo+seccion y bloques con NRC/hora/salon."""
    materias: list[MateriaExtraida] = []
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    DIAS_POR_ORDEN = ["L", "A", "M", "J", "V", "S"]

    for idx, linea in enumerate(lineas):
        m = re.match(r"^([A-Z]{2,6}[-\s]?\d{2,3})\s+(\d{2,3})\s+(.*)", linea, re.I)
        codigo: Optional[str] = None
        seccion = "-"
        resto = linea

        if m:
            codigo = m.group(1).upper().replace(" ", "-")
            seccion = m.group(2)
            resto = m.group(3) or ""
        else:
            nrc_match = re.search(r"\b(\d{5})\b", linea)
            if not nrc_match:
                continue
            codigo = f"X-{idx+1:03d}"

        horarios: list[HorarioSlot] = []
        nrc: Optional[str] = None
        salon: Optional[str] = None
        profesor: Optional[str] = None

        for hm in HORA_PATTERN.finditer(resto):
            par = _parse_hora(hm.group(0))
            if par:
                dia_idx = len(horarios) % len(DIAS_POR_ORDEN)
                horarios.append(HorarioSlot(
                    dia=DIAS_POR_ORDEN[dia_idx],
                    hora_inicio=par[0],
                    hora_fin=par[1],
                    aula=None,
                ))
        for hm in HORA_PATTERN_FLEX.finditer(resto):
            par = _parse_hora(hm.group(0))
            if par and not any(
                h.hora_inicio == par[0] and h.hora_fin == par[1] for h in horarios
            ):
                dia_idx = len(horarios) % len(DIAS_POR_ORDEN)
                horarios.append(HorarioSlot(
                    dia=DIAS_POR_ORDEN[dia_idx],
                    hora_inicio=par[0],
                    hora_fin=par[1],
                    aula=None,
                ))

        for token in re.split(r"[\s\-]+", resto):
            t = token.strip()
            if not t:
                continue
            if NRC_PATTERN.match(t):
                nrc = t
            elif SALON_PATTERN.match(t) or re.match(r"^\dCCO\d+", t, re.I):
                salon = t
            elif re.match(r"^[A-ZÁÉÍÓÚÑ][A-Za-z\s\-]+$", t) and len(t) > 6 and not t.isdigit():
                if not profesor or len(t) > len(profesor):
                    profesor = t

        nombre = resto
        for pat in [HORA_PATTERN, HORA_PATTERN_FLEX]:
            nombre = re.sub(pat.pattern, " ", nombre)
        nombre = re.sub(r"\d{5}\b", "", nombre).strip()
        nombre = re.sub(r"^\d+\s+", "", nombre).strip()
        nombre = re.sub(r"\s+", " ", nombre).strip()[:80] or (codigo or "Materia")

        if horarios or nombre or nrc:
            slots = [
                HorarioSlot(
                    dia=h.dia,
                    hora_inicio=h.hora_inicio,
                    hora_fin=h.hora_fin,
                    aula=salon or h.aula,
                )
                for h in horarios
            ]
            materias.append(MateriaExtraida(
                clave=codigo or f"X-{idx+1:03d}",
                grupo=seccion,
                nombre=nombre,
                nrc=nrc,
                profesor=profesor,
                horarios=slots,
            ))

    return materias


def _agrupar_por_nrc(materias: list[MateriaExtraida]) -> list[MateriaExtraida]:
    """Agrupa materias por NRC y asigna dias correctos a cada slot (L, A, M, J, V, S)."""
    from collections import defaultdict
    DIAS = ["L", "A", "M", "J", "V", "S"]
    grupos: dict[str, list[MateriaExtraida]] = defaultdict(list)
    for m in materias:
        nrc = m.nrc or f"__{m.clave}-{m.grupo}__"
        grupos[nrc].append(m)

    out: list[MateriaExtraida] = []
    for nrc, grupo in grupos.items():
        all_slots: list[tuple[str, str, str | None]] = []
        best_nombre = ""
        best_clave = ""
        best_grupo = ""
        best_profesor: Optional[str] = None

        for m in grupo:
            for h in m.horarios:
                all_slots.append((h.hora_inicio, h.hora_fin, h.aula))
            if m.nombre and not m.nombre.startswith("-") and len(m.nombre) > 3:
                if not best_nombre or (len(m.nombre) > len(best_nombre) and "1CCO" not in m.nombre):
                    best_nombre = m.nombre
            if m.clave and m.clave.startswith(("I", "F", "A", "R", "C")):
                best_clave = m.clave
            if m.grupo and m.grupo != "-":
                best_grupo = m.grupo
            if m.profesor:
                best_profesor = m.profesor

        seen: set[tuple[str, str, str | None]] = set()
        slots_ordenados = sorted(all_slots, key=lambda x: (x[0], x[1]))
        horarios_unicos: list[HorarioSlot] = []
        for i, (hi, hf, aula) in enumerate(slots_ordenados):
            key = (hi, hf, aula)
            if key in seen:
                continue
            seen.add(key)
            dia = DIAS[i % len(DIAS)]
            horarios_unicos.append(HorarioSlot(dia=dia, hora_inicio=hi, hora_fin=hf, aula=aula))

        nombre_final = best_nombre or (grupo[0].nombre if grupo else "Materia")
        clave_final = best_clave or (grupo[0].clave if grupo else None)
        grupo_final = best_grupo or (grupo[0].grupo if grupo else "-")

        out.append(MateriaExtraida(
            nrc=nrc if not nrc.startswith("__") else None,
            nombre=nombre_final,
            clave=clave_final,
            grupo=grupo_final,
            horarios=horarios_unicos,
            profesor=best_profesor,
        ))
    return out


def _rellenar_horarios_desde_nombre(materias: list[MateriaExtraida]) -> list[MateriaExtraida]:
    """Si una materia tiene horarios vacios pero el nombre contiene 0900-, etc., extraer."""
    out: list[MateriaExtraida] = []
    for m in materias:
        if m.horarios:
            out.append(m)
            continue
        texto = f"{m.nombre} {m.clave or ''}"
        horarios: list[HorarioSlot] = []
        for hm in HORA_PATTERN_FLEX.finditer(texto):
            par = _parse_hora(hm.group(0))
            if par:
                dia_idx = len(horarios) % 6
                horarios.append(HorarioSlot(
                    dia=["L", "A", "M", "J", "V", "S"][dia_idx],
                    hora_inicio=par[0],
                    hora_fin=par[1],
                    aula=None,
                ))
        if horarios:
            out.append(MateriaExtraida(
                nrc=m.nrc,
                nombre=m.nombre,
                clave=m.clave,
                grupo=m.grupo,
                horarios=horarios,
                profesor=m.profesor,
                creditos=m.creditos,
                aula=m.aula,
            ))
        else:
            out.append(m)
    return out


def parsear_horario_alumno_desde_bytes(
    contenido: bytes, nombre_archivo: str = "horario.pdf"
) -> list[MateriaExtraida]:
    """
    Parsea PDF de horario del alumno. Usa tablas primero, texto como fallback.
    Devuelve lista de MateriaExtraida.
    """
    lector = LectorPDF()
    contenido_pdf = lector.leer_desde_bytes(contenido)

    materias = _extraer_desde_tablas(contenido_pdf)
    if not materias and contenido_pdf.texto_completo:
        materias = _extraer_desde_texto(contenido_pdf.texto_completo)

    materias = _rellenar_horarios_desde_nombre(materias)
    materias = _agrupar_por_nrc(materias)

    if not materias and contenido_pdf.texto_completo:
        try:
            from app.services.ocr_pdf import extraer_texto_desde_bytes, ocr_disponible
            if ocr_disponible() and len((contenido_pdf.texto_completo or "").strip()) < 100:
                texto_ocr = extraer_texto_desde_bytes(contenido, dpi=200)
                if texto_ocr:
                    materias = _extraer_desde_texto(texto_ocr)
        except Exception:
            pass

    return materias
