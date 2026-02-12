"""
Normalización de datos extraídos de PDF (oferta y mapa curricular).

- Días: códigos BUAP (L, M, A, J, V, X, S) a código normalizado y nombre.
- Horas: siempre HH:MM (dos dígitos).
- Clave: forma normalizada para cruce (ej. "ITIS 601" -> "ITIS601").
"""
from app.models.schemas import (
    FilaOferta,
    HorarioSlot,
    MateriaExtraida,
    OfertaExtraida,
    normalizar_hora_militar,
)

# BUAP: L=Lunes, M=Martes, X=Miércoles, J=Jueves, V=Viernes, S=Sábado. A suele ser Miércoles en algunos sistemas.
DIAS_CODIGO_A_NOMBRE: dict[str, str] = {
    "L": "Lunes",
    "M": "Martes",
    "X": "Miércoles",
    "A": "Miércoles",
    "W": "Miércoles",
    "J": "Jueves",
    "V": "Viernes",
    "S": "Sábado",
    "D": "Domingo",
}


def normalizar_dia(codigo: str) -> tuple[str, str]:
    """
    Devuelve (codigo_normalizado, nombre).
    Codigo se deja en mayúscula de un caracter; nombre en español.
    """
    c = (codigo or "").strip().upper()
    if not c:
        return ("", "")
    if len(c) > 1:
        c = c[0]
    nombre = DIAS_CODIGO_A_NOMBRE.get(c, codigo.strip())
    return (c, nombre)


def normalizar_hora(h: str) -> str:
    """Asegura formato HH:MM (dos dígitos para hora y minuto)."""
    s = (h or "").strip()
    if not s:
        return "00:00"
    s = normalizar_hora_militar(s)
    if ":" in s:
        parts = s.split(":", 1)
        hh, mm = parts[0].zfill(2), (parts[1] if len(parts) > 1 else "00").zfill(2)
        return f"{hh}:{mm}"
    return s


def normalizar_clave(clave: str) -> str:
    """Clave sin espacios para cruce (ITIS 601 -> ITIS601)."""
    return (clave or "").replace(" ", "").strip().upper()


def normalizar_fila(f: FilaOferta) -> FilaOferta:
    """Normaliza una fila de oferta (días, horas)."""
    codigo, nombre_dia = normalizar_dia(f.dias)
    return FilaOferta(
        nrc=f.nrc.strip(),
        clave=f.clave.strip(),
        materia=f.materia.strip(),
        secc=f.secc.strip(),
        dias=codigo or f.dias,
        hora_inicio=normalizar_hora(f.hora_inicio),
        hora_fin=normalizar_hora(f.hora_fin),
        profesor=f.profesor.strip(),
        salon=f.salon.strip(),
    )


def normalizar_horario_slot(s: HorarioSlot) -> HorarioSlot:
    """Normaliza un slot de horario (dia a código + nombre opcional en dia)."""
    codigo, nombre = normalizar_dia(s.dia)
    return HorarioSlot(
        dia=nombre or codigo or s.dia,
        hora_inicio=normalizar_hora(s.hora_inicio),
        hora_fin=normalizar_hora(s.hora_fin),
    )


def normalizar_materia(m: MateriaExtraida) -> MateriaExtraida:
    """Normaliza una materia (horarios con día y hora)."""
    return MateriaExtraida(
        nombre=m.nombre.strip(),
        clave=(m.clave or "").strip() or None,
        grupo=(m.grupo or "").strip() or None,
        horarios=[normalizar_horario_slot(s) for s in m.horarios],
        profesor=(m.profesor or "").strip() or None,
        aula=(m.aula or "").strip() or None,
        creditos=m.creditos,
    )


def normalizar_oferta(oferta: OfertaExtraida) -> OfertaExtraida:
    """Normaliza filas y materias de una oferta extraída."""
    return OfertaExtraida(
        filas=[normalizar_fila(f) for f in oferta.filas],
        materias=[normalizar_materia(m) for m in oferta.materias],
        archivos_procesados=list(oferta.archivos_procesados),
    )
