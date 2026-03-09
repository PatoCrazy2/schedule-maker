import { Document, Page, View, Text, StyleSheet } from "@react-pdf/renderer"
import type { MateriaExtraida } from "@/types/api"

// ─── Paleta de colores (equivalentes RGB a los Tailwind bg-*-200) ─────────────
const COLORES_PDF: Record<string, string> = {
    "bg-blue-200": "#bfdbfe",
    "bg-green-200": "#bbf7d0",
    "bg-amber-200": "#fde68a",
    "bg-purple-200": "#e9d5ff",
    "bg-rose-200": "#fecdd3",
    "bg-cyan-200": "#a5f3fc",
}

function colorHex(tailwindClass: string): string {
    return COLORES_PDF[tailwindClass] ?? "#e5e7eb"
}

// ─── Tipos ───────────────────────────────────────────────────────────────────
export interface MateriaConColor {
    materia: MateriaExtraida
    color: string
}

interface HorarioDocumentProps {
    showCalendar: boolean
    materiasConColor: MateriaConColor[]
    horas: number[]
    diasOrden: string[]
    diasNombres: (dia: string) => string
    formatHorario: (dia: string, hi: string, hf: string, aula?: string) => string
    selectedMaterias: MateriaExtraida[]
}

// ─── Estilos ─────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
    page: {
        fontFamily: "Helvetica",
        padding: 24,
        backgroundColor: "#ffffff",
        fontSize: 8,
    },
    titulo: {
        fontSize: 14,
        fontFamily: "Helvetica-Bold",
        marginBottom: 12,
        color: "#111827",
    },

    // ── Grid / tabla ──────────────────────────────────────────────────────────
    gridHeader: {
        flexDirection: "row",
        backgroundColor: "#f3f4f6",
        borderTopWidth: 1,
        borderLeftWidth: 1,
        borderColor: "#d1d5db",
    },
    gridRow: {
        flexDirection: "row",
        borderLeftWidth: 1,
        borderColor: "#d1d5db",
    },
    horaCell: {
        width: 56,
        borderRightWidth: 1,
        borderBottomWidth: 1,
        borderColor: "#d1d5db",
        padding: 3,
        justifyContent: "center",
    },
    headerCell: {
        flex: 1,
        borderRightWidth: 1,
        borderBottomWidth: 1,
        borderColor: "#d1d5db",
        padding: 3,
        alignItems: "center",
    },
    diaCell: {
        flex: 1,
        borderRightWidth: 1,
        borderBottomWidth: 1,
        borderColor: "#d1d5db",
        padding: 3,
        minHeight: 28,
    },
    horaCellText: {
        fontSize: 7,
        color: "#374151",
        fontFamily: "Helvetica-Bold",
    },
    headerCellText: {
        fontSize: 7,
        color: "#374151",
        fontFamily: "Helvetica-Bold",
    },
    materiaNombre: {
        fontSize: 6,
        fontFamily: "Helvetica-Bold",
        color: "#1f2937",
        marginBottom: 1,
    },
    materiaGrupo: {
        fontSize: 5.5,
        color: "#374151",
    },
    materiaAula: {
        fontSize: 5.5,
        color: "#374151",
    },

    // ── Vista lista ───────────────────────────────────────────────────────────
    listaCard: {
        borderWidth: 1,
        borderColor: "#d1d5db",
        borderRadius: 4,
        padding: 8,
        marginBottom: 8,
        backgroundColor: "#f9fafb",
    },
    listaNombre: {
        fontSize: 10,
        fontFamily: "Helvetica-Bold",
        color: "#111827",
        marginBottom: 2,
    },
    listaProfesor: {
        fontSize: 8,
        color: "#6b7280",
        marginBottom: 4,
    },
    listaBadge: {
        backgroundColor: "#e5e7eb",
        borderRadius: 3,
        paddingTop: 2,
        paddingBottom: 2,
        paddingLeft: 5,
        paddingRight: 5,
        marginRight: 4,
        marginTop: 2,
    },
    listaBadgeText: {
        fontSize: 7,
        color: "#374151",
    },
    listaBadgesRow: {
        flexDirection: "row",
        flexWrap: "wrap",
    },
})

// ─── Lógica de celda (idéntica a la de la tabla HTML) ────────────────────────
function getCeldaInfo(
    hora: number,
    dia: string,
    materiasConColor: MateriaConColor[]
): { materia: MateriaExtraida; color: string; slot: MateriaExtraida["horarios"][0] } | null {
    for (const { materia, color } of materiasConColor) {
        const slot = (materia.horarios ?? []).find((s) => {
            const slotDia = s.dia.length === 1 ? s.dia : s.dia[0]
            const [hiH] = (s.hora_inicio || "00:00").split(":")
            const [hfH, hfM] = (s.hora_fin || "00:00").split(":")
            const hiNum = parseInt(hiH || "0", 10)
            const hfNumRaw = parseInt(hfH || "0", 10)
            const hfMin = parseInt(hfM || "0", 10)
            const hfNum = hfMin > 0 ? hfNumRaw + 1 : hfNumRaw
            return slotDia === dia && hora >= hiNum && hora < hfNum
        })
        if (slot) return { materia, color, slot }
    }
    return null
}

// ─── Componente principal ─────────────────────────────────────────────────────
export function HorarioDocument({
    showCalendar,
    materiasConColor,
    horas,
    diasOrden,
    diasNombres,
    formatHorario,
    selectedMaterias,
}: HorarioDocumentProps) {
    return (
        <Document>
            {showCalendar ? (
                // ──────────────── Vista Calendario (horizontal) ────────────────────
                <Page size="A4" orientation="landscape" style={s.page}>
                    <Text style={s.titulo}>Schedule-Maker</Text>

                    {/* Cabecera de días */}
                    <View style={s.gridHeader}>
                        <View style={s.horaCell}>
                            <Text style={s.horaCellText}>Hora</Text>
                        </View>
                        {diasOrden.map((d) => (
                            <View key={d} style={s.headerCell}>
                                <Text style={s.headerCellText}>{diasNombres(d)}</Text>
                            </View>
                        ))}
                    </View>

                    {/* Filas de horas */}
                    {horas.map((hora) => (
                        <View key={hora} style={s.gridRow}>
                            {/* Columna hora */}
                            <View style={s.horaCell}>
                                <Text style={s.horaCellText}>
                                    {hora}:00{"\n"}{hora + 1}:00
                                </Text>
                            </View>

                            {/* Celdas de días */}
                            {diasOrden.map((dia) => {
                                const info = getCeldaInfo(hora, dia, materiasConColor)
                                return (
                                    <View
                                        key={dia}
                                        style={[
                                            s.diaCell,
                                            info ? { backgroundColor: colorHex(info.color) } : {},
                                        ]}
                                    >
                                        {info && (
                                            <>
                                                <Text style={s.materiaNombre}>
                                                    {info.materia.nombre}
                                                </Text>
                                                <Text style={s.materiaGrupo}>
                                                    Grp: {info.materia.grupo}
                                                </Text>
                                                {info.slot.aula && (
                                                    <Text style={s.materiaAula}>
                                                        Salón: {info.slot.aula}
                                                    </Text>
                                                )}
                                            </>
                                        )}
                                    </View>
                                )
                            })}
                        </View>
                    ))}
                </Page>
            ) : (
                // ──────────────── Vista Lista (vertical) ───────────────────────────
                <Page size="A4" orientation="portrait" style={s.page}>
                    <Text style={s.titulo}>Horario — Lista de materias</Text>

                    {selectedMaterias.map((m, i) => (
                        <View key={`${m.nrc}-${m.grupo}-${i}`} style={s.listaCard}>
                            <Text style={s.listaNombre}>
                                {m.nombre}  ·  {m.clave}  ·  NRC {m.nrc}
                            </Text>
                            {m.profesor ? (
                                <Text style={s.listaProfesor}>{m.profesor}</Text>
                            ) : null}
                            <View style={s.listaBadgesRow}>
                                {(m.horarios ?? []).map((h, j) => (
                                    <View key={j} style={s.listaBadge}>
                                        <Text style={s.listaBadgeText}>
                                            {formatHorario(h.dia, h.hora_inicio, h.hora_fin, h.aula)}
                                        </Text>
                                    </View>
                                ))}
                            </View>
                        </View>
                    ))}
                </Page>
            )}
        </Document>
    )
}
