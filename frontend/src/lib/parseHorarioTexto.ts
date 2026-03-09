/**
 * Parser heuristico para horarios de alumnos BUAP escaneados/pegados.
 * Detecta codigo, seccion, materia y bloques horarios por dia.
 */

export interface SlotHorario {
  dia: string
  horaInicio: string
  horaFin: string
  aula?: string
}

export interface MateriaParsed {
  codigo: string
  seccion: string
  materia: string
  slots: SlotHorario[]
  profesor?: string
  nrc?: string
  salon?: string
}

/** Patron para codigo de materia: ITIS-252, CCOS 260, FGUS 006, IDDS 001 */
const CODIGO_REGEX = /^([A-Z]{2,6}[-\s]?\d{2,3})\s+(\d{2,3})\s*(.*)/i

/** Patron para rango de hora: 0900-1059, 11:00-12:59 */
const HORA_REGEX = /(\d{1,2}):?(\d{2})-(\d{1,2}):?(\d{2})|(\d{4})-(\d{4})/

/** Columna de token -> dia (cabecera: CODIGO SEC MATERIAS LUNES MARTES ...) */
const DIAS_POSICION_FILA_MATERIA: Record<number, string> = {
  3: "L",
  4: "A",
  5: "X",
  6: "J",
  7: "V",
  8: "S",
  9: "D",
}

/** Fila solo horarios: token 0 = LUNES, 1 = MARTES, ... */
const DIAS_POSICION_FILA_HORARIOS: Record<number, string> = {
  0: "L",
  1: "A",
  2: "X",
  3: "J",
  4: "V",
  5: "S",
  6: "D",
}

function normalizarHora(m: string): string {
  const s = m.trim()
  if (s.length === 4) return `${s.slice(0, 2)}:${s.slice(2)}`
  if (s.length === 5 && s[2] === ":") return s
  return s
}

function parseHoraFromMatch(match: RegExpMatchArray): { inicio: string; fin: string } {
  if (match[1] !== undefined) {
    return {
      inicio: `${match[1].padStart(2, "0")}:${match[2]}`,
      fin: `${match[3].padStart(2, "0")}:${match[4]}`,
    }
  }
  if (match[5] !== undefined) {
    return {
      inicio: normalizarHora(match[5]),
      fin: normalizarHora(match[6]),
    }
  }
  return { inicio: "", fin: "" }
}

function esCodigoMateria(s: string): boolean {
  return /^[A-Z]{2,6}[-\s]?\d{2,3}$/i.test(s.trim())
}

function esSeccion(s: string): boolean {
  return /^\d{2,3}$/.test(s.trim()) && s.length <= 4
}

function extraerNombreMateria(resto: string): string {
  return resto
    .replace(/\d{4}-\d{4}/g, "")
    .replace(/\d{1,2}:\d{2}-\d{1,2}:\d{2}/g, "")
    .replace(/^[\d\s-]+/, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 80) || ""
}

/** Extrae materias y slots desde texto pegado de horario escaneado. */
export function parsearHorarioTexto(texto: string): MateriaParsed[] {
  const lineas = texto
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean)

  if (lineas.length === 0) return []

  let inicioContenido = 0
  for (let i = 0; i < Math.min(5, lineas.length); i++) {
    const u = lineas[i].toUpperCase()
    if (
      (u.includes("CODIGO") || u.includes("CÓDIGO")) &&
      (u.includes("LUNES") || u.includes("MATERIA"))
    ) {
      inicioContenido = i + 1
      break
    }
  }

  const lineasDatos = lineas.slice(inicioContenido)
  const materias: MateriaParsed[] = []
  let materiaActual: MateriaParsed | null = null

  for (const linea of lineasDatos) {
    const tokens = linea.split(/\s{2,}|\t/).filter(Boolean)
    if (tokens.length < 2) continue

    const t0 = tokens[0]
    const t1 = tokens[1]

    if (esCodigoMateria(t0) && esSeccion(t1)) {
      if (materiaActual && (materiaActual.slots.length > 0 || materiaActual.materia)) {
        materias.push(materiaActual)
      }
      const codigo = t0.toUpperCase().replace(/\s+/, "-")
      const seccion = t1
      const resto = tokens.slice(2).join(" ")
      const slots: SlotHorario[] = []

      for (let j = 2; j < tokens.length; j++) {
        const t = tokens[j]
        const hm = t.match(HORA_REGEX)
        if (hm && t !== "-") {
          const { inicio, fin } = parseHoraFromMatch(hm)
          const dia = DIAS_POSICION_FILA_MATERIA[j] ?? DIAS_POSICION_FILA_HORARIOS[j - 3] ?? "L"
          slots.push({ dia, horaInicio: inicio, horaFin: fin })
        }
      }

      materiaActual = {
        codigo,
        seccion,
        materia: extraerNombreMateria(resto) || codigo,
        slots,
      }
      continue
    }

    if (materiaActual) {
      for (const t of tokens) {
        if (/^\d{5}$/.test(t)) materiaActual.nrc = t
        if (/^[\dA-Z]+\/\d+$/.test(t) || /^\dCCO\d+\/\d+$/i.test(t))
          materiaActual.salon = t
        if (
          /^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-z\s-]+[A-ZÁÉÍÓÚÑa-z]$/.test(t) &&
          t.length > 8 &&
          !HORA_REGEX.test(t)
        )
          materiaActual.profesor = t
        const hm = t.match(HORA_REGEX)
        if (hm && t !== "-") {
          const { inicio, fin } = parseHoraFromMatch(hm)
          const idx = tokens.indexOf(t)
          const dia =
            DIAS_POSICION_FILA_HORARIOS[idx] ??
            DIAS_POSICION_FILA_MATERIA[idx] ??
            materiaActual.slots[0]?.dia ??
            "L"
          materiaActual.slots.push({ dia, horaInicio: inicio, horaFin: fin })
        }
      }
    }
  }

  if (materiaActual && (materiaActual.slots.length > 0 || materiaActual.materia)) {
    materias.push(materiaActual)
  }

  if (materias.length === 0) return parsearHorarioLineal(lineas)

  return materias
}

/** Fallback: parseo por lineas que contengan codigo + seccion + hora en misma linea */
function parsearHorarioLineal(lineas: string[]): MateriaParsed[] {
  const materias: MateriaParsed[] = []
  const vistos = new Set<string>()

  for (const linea of lineas) {
    const m = linea.match(CODIGO_REGEX)
    if (!m) continue

    const codigo = m[1].toUpperCase().replace(/\s+/, "-")
    const seccion = m[2]
    const resto = m[3] ?? ""
    const key = `${codigo}-${seccion}`
    if (vistos.has(key)) continue

    const slots: SlotHorario[] = []
    const horaIter = resto.matchAll(/(\d{4})-(\d{4})|(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})/g)
    for (const hm of horaIter) {
      let inicio: string
      let fin: string
      if (hm[1]) {
        inicio = normalizarHora(hm[1])
        fin = normalizarHora(hm[2])
      } else {
        inicio = `${hm[3]!.padStart(2, "0")}:${hm[4]}`
        fin = `${hm[5]!.padStart(2, "0")}:${hm[6]}`
      }
      slots.push({ dia: DIAS_POSICION_FILA_HORARIOS[slots.length] ?? "L", horaInicio: inicio, horaFin: fin })
    }

    const nombre = extraerNombreMateria(resto)
    if (nombre || slots.length > 0) {
      vistos.add(key)
      materias.push({
        codigo,
        seccion,
        materia: nombre || codigo,
        slots,
      })
    }
  }

  return materias
}
