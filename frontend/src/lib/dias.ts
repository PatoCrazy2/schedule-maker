/** Codigos de dia BUAP -> nombre completo. Variables globales, no cambian. */
export const DIAS_BUAP: Record<string, string> = {
  L: "Lunes",
  A: "Martes",
  M: "Miércoles",
  J: "Jueves",
  V: "Viernes",
  S: "Sábado",
  D: "Domingo",
  X: "Miércoles",
  W: "Miércoles",
}

/** Convierte "L", "L,M,J" o "L M J" en "Lunes", "Lunes, Martes, Jueves" */
export function diasToNombres(dias: string): string {
  const parts = (dias || "").split(/[,;\s]+/).map((p) => p.trim().toUpperCase())
  if (parts.length === 0 || (parts.length === 1 && !parts[0])) return ""
  return parts.map((c) => DIAS_BUAP[c] ?? c).filter(Boolean).join(", ")
}
