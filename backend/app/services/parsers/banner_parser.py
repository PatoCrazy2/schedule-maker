"""
Parser para PDF de oferta tipo Banner BUAP.

Formato objetivo por fila: NRC, Clave, Materia, Secc, Dias, Hora, Profesor, Salon.
Ejemplo: 50030 CCOS 260 Redes de Computadoras OO1 L 1000-1059 TREVINO - SANCHEZ DANIEL 1CCO4/305
"""
import re
from typing import Optional

from app.models.schemas import (
    FilaOferta,
    HorarioSlot,
    MateriaExtraida,
    normalizar_hora_militar,
)
from app.services.lector_pdf import ContenidoPDF
from app.services.parsers.base_parser import BaseOfertaParser

# Encabezados que no son datos
ENCABEZADOS = frozenset(
    {"NRC", "CLAVE", "MATERIA", "SECC", "DIAS", "DÍA", "HORA", "PROFESOR", "SALON", "SALÓN", "CRÉDITOS"}
)


class BannerOfertaParser(BaseOfertaParser):
    """Parser para ofertas Banner BUAP: columnas NRC, Clave, Materia, Secc, Dias, Hora, Profesor, Salon."""

    def puede_parsear(self, contenido: ContenidoPDF, nombre_archivo: str = "") -> bool:
        if contenido.tablas_por_pagina and any(t for t in contenido.tablas_por_pagina):
            return True
        texto = (contenido.texto_completo or "").upper()
        if "BANNER" in nombre_archivo.upper():
            return True
        if re.search(r"NRC|CLAVE|SECC|LUNES|MARTES|HORA|GRUPO|MATERIA", texto):
            return True
        return False

    def extraer_filas(
        self, contenido: ContenidoPDF, nombre_archivo: str = ""
    ) -> list[FilaOferta]:
        """Extrae filas con columnas: NRC, Clave, Materia, Secc, Dias, Hora, Profesor, Salon (índices 0-7)."""
        filas: list[FilaOferta] = []
        for tablas in contenido.tablas_por_pagina:
            for table in tablas:
                for row in table:
                    f = self._row_to_fila(row)
                    if f:
                        filas.append(f)
        if not filas and contenido.texto_completo:
            filas = self._extraer_filas_desde_texto(contenido.texto_completo)
        return filas

    def _row_to_fila(self, row: list[str]) -> Optional[FilaOferta]:
        """Convierte una fila de tabla en FilaOferta. Columnas: 0=NRC, 1=Clave, 2=Materia, 3=Secc, 4=Dias, 5=Hora, 6=Profesor, 7=Salon."""
        r = [str(c).strip() for c in row]
        if len(r) < 8 or all(not c for c in r):
            return None
        nrc = r[0] or ""
        clave = r[1] or ""
        materia = r[2] or ""
        secc = r[3] or ""
        dias = r[4] or ""
        hora_raw = r[5] or ""
        profesor = r[6] or ""
        salon = r[7] or ""
        if not nrc or not materia or _es_encabezado(nrc) or _es_encabezado(materia):
            return None
        hora_inicio, hora_fin = _parsear_rango_hora(hora_raw)
        if not hora_inicio:
            hora_inicio = "00:00"
            hora_fin = "00:00"
        return FilaOferta(
            nrc=nrc,
            clave=clave,
            materia=materia,
            secc=secc,
            dias=dias,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            profesor=profesor,
            salon=salon,
        )

    def _extraer_filas_desde_texto(self, texto: str) -> list[FilaOferta]:
        """
        Líneas tipo: 50030 CCOS 260 Redes de Computadoras OO1 L 1000-1059 TREVINO - SANCHEZ DANIEL 1CCO4/305
        Parseo: hora (1000-1059), luego salon (ultimo token), profesor (resto), luego izquierda: nrc, clave+materia, secc, dias.
        """
        filas = []
        hora_pat = re.compile(r"(\d{4}-\d{4})")
        for line in texto.splitlines():
            line = line.strip()
            if not line or len(line) < 30:
                continue
            hm = hora_pat.search(line)
            if not hm:
                continue
            hora_rango = hm.group(1)
            hi, hf = _parsear_rango_hora(hora_rango)
            if not hi:
                continue
            pos = hm.start()
            izq = line[:pos].strip()
            der = line[pos + len(hora_rango):].strip()
            if not der:
                continue
            parts_der = der.rsplit(maxsplit=1)
            salon = parts_der[-1] if len(parts_der) == 2 else ""
            profesor = parts_der[0] if len(parts_der) == 2 else der
            if not izq:
                continue
            parts_izq = izq.split()
            if len(parts_izq) < 4:
                continue
            nrc = parts_izq[0]
            if not nrc.isdigit() or len(nrc) != 5:
                continue
            secc = parts_izq[-2]
            dias = parts_izq[-1]
            if len(dias) != 1 or dias.upper() not in "LMAJVIBSD":
                continue
            clave_materia = parts_izq[1:-2]
            if len(clave_materia) >= 2:
                clave = f"{clave_materia[0]} {clave_materia[1]}"
                materia = " ".join(clave_materia[2:])
            else:
                clave = clave_materia[0] if clave_materia else ""
                materia = " ".join(clave_materia[1:])
            if not materia:
                materia = clave or "Sin nombre"
            filas.append(
                FilaOferta(
                    nrc=nrc,
                    clave=clave,
                    materia=materia,
                    secc=secc,
                    dias=dias.upper(),
                    hora_inicio=hi,
                    hora_fin=hf,
                    profesor=profesor,
                    salon=salon,
                )
            )
        return filas

    def extraer_materias(
        self, contenido: ContenidoPDF, nombre_archivo: str = ""
    ) -> list[MateriaExtraida]:
        """Construye materias agrupando filas por (nrc, clave, materia, secc)."""
        filas = self.extraer_filas(contenido, nombre_archivo)
        return _filas_a_materias(filas)


def _es_encabezado(celda: str) -> bool:
    return (celda or "").upper().strip() in ENCABEZADOS


def _parsear_rango_hora(s: str) -> tuple[str, str]:
    """Convierte '1000-1059' o '0900-1059' en (hora_inicio, hora_fin) normalizadas."""
    s = (s or "").strip()
    if not s:
        return ("", "")
    partes = re.split(r"[\s\-–—]+", s)
    if len(partes) >= 2:
        hi = normalizar_hora_militar(partes[0])
        hf = normalizar_hora_militar(partes[1])
        if hi and hf:
            return (hi, hf)
    if len(partes) == 1 and partes[0]:
        hi = normalizar_hora_militar(partes[0])
        return (hi, hi)
    return ("", "")


def _filas_a_materias(filas: list[FilaOferta]) -> list[MateriaExtraida]:
    """Agrupa filas por (nrc, clave, materia, secc) en MateriaExtraida con horarios."""
    from collections import defaultdict
    grupos: dict[tuple[str, str, str, str], list[FilaOferta]] = defaultdict(list)
    for f in filas:
        key = (f.nrc, f.clave, f.materia, f.secc)
        grupos[key].append(f)
    materias = []
    for (nrc, clave, materia, secc), grupo in grupos.items():
        horarios = [
            HorarioSlot(
                dia=f.dias,
                hora_inicio=f.hora_inicio,
                hora_fin=f.hora_fin,
            )
            for f in grupo
        ]
        profesor = grupo[0].profesor if grupo else ""
        aula = grupo[0].salon if grupo else ""
        materias.append(
            MateriaExtraida(
                nombre=materia,
                clave=clave,
                grupo=secc,
                horarios=horarios,
                profesor=profesor or None,
                aula=aula or None,
            )
        )
    return materias
