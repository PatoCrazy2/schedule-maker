import type { HorarioSlot, MateriaExtraida } from "@/types/api"

/**
 * Convierte un string de hora "HH:MM" a minutos para facilitar comparaciones numéricas.
 * Ejemplo "07:30" => 450
 */
export function timeToMinutes(timeStr: string): number {
    if (!timeStr) return 0
    const parts = timeStr.split(":")
    if (parts.length < 2) return 0
    const hours = parseInt(parts[0], 10)
    const minutes = parseInt(parts[1], 10)
    if (isNaN(hours) || isNaN(minutes)) return 0
    return hours * 60 + minutes
}

/**
 * Verifica si dos HorarioSlot se cruzan en tiempo y día.
 * Se cruzan si (dia_A == dia_B) Y (inicio_A < fin_B AND inicio_B < fin_A)
 * (A != B asumido)
 */
export function slotsOverlap(a: HorarioSlot, b: HorarioSlot): boolean {
    // Manejo de días compuestos (ej. "LA" o arreglos, el backend extrae "L").
    // En nuestro DTO "dia" es 1 char. Si choca alguna letra del string, cuenta como mismo día.
    const aDays = a.dia.split("")
    const bDays = b.dia.split("")
    const sameDay = aDays.some((d) => bDays.includes(d))

    if (!sameDay) return false

    const startA = timeToMinutes(a.hora_inicio)
    const endA = timeToMinutes(a.hora_fin)
    const startB = timeToMinutes(b.hora_inicio)
    const endB = timeToMinutes(b.hora_fin)

    return startA < endB && startB < endA
}

/**
 * Revisa si los horarios de dos materias se cruzan.
 */
export function materiasOverlap(m1: MateriaExtraida, m2: MateriaExtraida): boolean {
    if (!m1.horarios || !m2.horarios) return false

    for (const slot1 of m1.horarios) {
        for (const slot2 of m2.horarios) {
            if (slotsOverlap(slot1, slot2)) {
                return true
            }
        }
    }
    return false
}

/**
 * Función atómica a nivel horario que evalúa si `newMateria`
 * puede ser agregada al array `currentSchedule`.
 */
export function canAddMateria(
    newMateria: MateriaExtraida,
    currentSchedule: MateriaExtraida[]
): { allowed: boolean; reason?: string } {
    // 1. Validar duplicidad de materia (misma clave o nombre)
    const claveONombre = newMateria.clave || newMateria.nombre
    for (const block of currentSchedule) {
        // Caso de uso: El usuario intenta meter 2 grupos de "Cálculo".
        const blockClaveONombre = block.clave || block.nombre
        if (blockClaveONombre === claveONombre) {
            return {
                allowed: false,
                reason: `Ya seleccionaste un grupo para la materia: ${blockClaveONombre}`,
            }
        }
    }

    // 2. Validar solapamiento de horario (Time collision)
    for (const block of currentSchedule) {
        if (materiasOverlap(newMateria, block)) {
            return {
                allowed: false,
                reason: `Se cruza con el horario de ${block.nombre} (${block.grupo})`,
            }
        }
    }

    return { allowed: true }
}
