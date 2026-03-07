"""
Parser para PDF de oferta tipo CU2 BUAP.

Formato objetivo por fila: NRC, Clave, Materia, Secc, Campus, Dias, Hora, Profesor, Salon.
Ejemplo: 50030 CCOS 260 Redes de Computadoras OO1 CU2 L 1000-1059 TREVINO - SANCHEZ DANIEL 1CCO4/305
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
    {"NRC", "CLAVE", "MATERIA", "SECC", "CAMPUS", "DIAS", "DÍA", "HORA", "PROFESOR", "SALON", "SALÓN", "CRÉDITOS"}
)


class Cu2OfertaParser(BaseOfertaParser):
    """Parser para ofertas CU2 BUAP: columnas NRC, Clave, Materia, Secc, Campus, Dias, Hora, Profesor, Salon."""

    def puede_parsear(self, contenido: ContenidoPDF, nombre_archivo: str = "") -> bool:
        texto = (contenido.texto_completo or "").upper()
        
        # 1. Verificación estricta: debe contener estrictamente TODAS las 9 palabras base
        palabras_encontradas = set(re.findall(r"NRC|CLAVE|MATERIA|SECC|CAMPUS|DIAS|HORA|PROFESOR|SALON", texto))
        if len(palabras_encontradas) != 9:
            return False
            
        # 2. Si no hay tablas, se rechaza inmediatamente
        if not contenido.tablas_por_pagina or not any(t for t in contenido.tablas_por_pagina):
            return False
            
        # 3. Validar estrictamente que la tabla tenga solo 9 columnas
        for pag in contenido.tablas_por_pagina:
            for tabla in pag:
                if tabla and len(tabla) > 0 and len(tabla[0]) == 9:
                    return True
                    
        return False

    def extraer_filas(
        self, contenido: ContenidoPDF, nombre_archivo: str = ""
    ) -> list[FilaOferta]:
        """Extrae filas con columnas: NRC, Clave, Materia, Secc, Campus, Dias, Hora, Profesor, Salon (índices 0-8)."""
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
        """Convierte una fila de tabla en FilaOferta. Columnas: 0=NRC, 1=Clave, 2=Materia, 3=Secc, 4=Campus, 5=Dias, 6=Hora, 7=Profesor, 8=Salon."""
        r = [str(c).strip() for c in row]
        if len(r) < 9 or all(not c for c in r):
            return None
        nrc = r[0] or ""
        clave = r[1] or ""
        materia = r[2] or ""
        secc = r[3] or ""
        # campus = r[4] or ""  Se ignora a nivel de FilaOferta
        dias = r[5] or ""
        hora_raw = r[6] or ""
        profesor = r[7] or ""
        salon = r[8] or ""
        
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
        Líneas tipo: 50030 CCOS 260 Redes de Computadoras OO1 CU2 L 1000-1059 TREVINO - SANCHEZ DANIEL 1CCO4/305
        Parseo aproximado asumiendo un espacio extra por el campus.
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
            if len(parts_izq) < 5:  # Necesitamos NRC, Clave(1 o 2), Materia, Secc, Campus, Dias
                continue
            nrc = parts_izq[0]
            if not nrc.isdigit() or len(nrc) != 5:
                continue
            
            # parts_izq[-1] = Dias
            # parts_izq[-2] = Campus (e.g. CU2)
            # parts_izq[-3] = Secc
            dias = parts_izq[-1]
            if len(dias) != 1 or dias.upper() not in "LMAJVIBSD":
                continue
            
            # Extraer secc asumiendo que el penúltimo es campus y antepenúltimo es secc
            secc = parts_izq[-3]
            
            clave_materia = parts_izq[1:-3]
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

    def extraer_metadata(self, contenido: ContenidoPDF) -> dict:
        """
        Extrae facultad, carrera, campus y periodo del texto del PDF tipo CU2.
        """
        texto = contenido.texto_completo or ""
        metadata = {
            "facultad": None,
            "carrera": None,
            "campus": None,
            "periodo": None
        }
        
        facultad_match = re.search(r"(?i)(Facultad de[^\r\n]*)", texto)
        if facultad_match:
            metadata["facultad"] = facultad_match.group(1).strip()
            
        carrera_campus_match = re.search(r"(?i)([^\r\n]+?)\s*-\s*CAMPUS\s*([^\r\n]*)", texto)
        if carrera_campus_match:
            metadata["carrera"] = carrera_campus_match.group(1).strip()
            metadata["campus"] = carrera_campus_match.group(2).strip()

        periodo_match = re.search(r"(?i)PROGRAMACI[OÓ]N ACAD[EÉ]MICA\s*-\s*([^\r\n]*)", texto)
        if periodo_match:
            metadata["periodo"] = periodo_match.group(1).strip()

        return metadata


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
        horarios = []
        for f in grupo:
            dias_raw = (f.dias or "").upper()
            dias_validos = [d for d in dias_raw if d in "LAMJVSDXW"]
            if not dias_validos:
                dias_validos = [dias_raw.strip()] if dias_raw.strip() else []
                
            for dia_letra in dias_validos:
                horarios.append(
                    HorarioSlot(
                        dia=dia_letra,
                        hora_inicio=f.hora_inicio,
                        hora_fin=f.hora_fin,
                        aula=f.salon or None,
                    )
                )

        profesor = grupo[0].profesor if grupo else ""
        salon = grupo[0].salon if grupo else ""
        materias.append(
            MateriaExtraida(
                nrc=nrc,
                nombre=materia,
                clave=clave,
                grupo=secc,
                horarios=horarios,
                profesor=profesor or None,
                aula=salon or None,
                creditos=None,
            )
        )
    return materias
