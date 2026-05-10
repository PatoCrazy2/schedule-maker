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

const DIAS_CORTO: Record<string, string> = {
    Lunes: "Lun",
    Martes: "Mar",
    Miercoles: "Mie",
    "Miércoles": "Mie",
    Jueves: "Jue",
    Viernes: "Vie",
    Sabado: "Sab",
    "Sábado": "Sab",
    Domingo: "Dom",
}

function diaCorto(diaCode: string, diasNombresFn: (d: string) => string): string {
    const full = diasNombresFn(diaCode)
    return DIAS_CORTO[full] ?? full.slice(0, 3)
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
        width: 55,
        borderRightWidth: 1,
        borderBottomWidth: 1,
        borderColor: "#d1d5db",
        padding: 3,
        justifyContent: "center",
        backgroundColor: "#f9fafb",
    },
    headerCell: {
        flex: 1,
        flexBasis: 0,
        borderRightWidth: 1,
        borderBottomWidth: 1,
        borderColor: "#d1d5db",
        padding: 3,
        alignItems: "center",
        justifyContent: "center",
    },
    diaCell: {
        flex: 1,
        flexBasis: 0,
        borderRightWidth: 1,
        borderBottomWidth: 1,
        borderColor: "#d1d5db",
        padding: 3,
        minHeight: 28,
        position: "relative", // Necesario para la barra absoluta
    },
    colorBar: {
        position: "absolute",
        left: 0,
        top: 0,
        bottom: 0,
        width: 4,
    },
    contentWrapper: {
        paddingLeft: 4, // Espacio para que el texto no toque la barra
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

    // ── Referencia de materias ─────────────────────────────────────────────
    refTitulo: {
        fontSize: 9,
        fontFamily: "Helvetica-Bold",
        marginTop: 12,
        marginBottom: 6,
        color: "#6b7280",
    },
    refGrid: {
        flexDirection: "row",
        flexWrap: "wrap",
    },
    refCard: {
        flexDirection: "row",
        borderWidth: 1,
        borderColor: "#d1d5db",
        borderRadius: 4,
        padding: 6,
        marginBottom: 4,
        width: "32%",
        minWidth: 130,
        backgroundColor: "#ffffff",
    },
    refColorBar: {
        width: 4,
        marginRight: 8,
        borderRadius: 2,
    },
    refMateria: {
        fontSize: 9,
        fontFamily: "Helvetica-Bold",
        color: "#111827",
        marginBottom: 2,
    },
    refNrc: {
        fontSize: 7,
        fontFamily: "Helvetica-Bold",
        color: "#374151",
        marginBottom: 4,
    },
    refSlot: {
        flexDirection: "row",
        justifyContent: "space-between",
        marginBottom: 2,
        fontSize: 6,
        color: "#6b7280",
    },
    refSalon: {
        fontFamily: "Helvetica-Bold",
        color: "#111827",
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
                            <View style={s.horaCell}>
                                <Text style={s.horaCellText}>
                                    {hora}:00{"\n"}{hora + 1}:00
                                </Text>
                            </View>
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
                                                {/* Barra de color absoluta: no afecta al layout */}
                                                <View 
                                                    style={[
                                                        s.colorBar, 
                                                        { backgroundColor: colorHex(info.color), opacity: 0.8 }
                                                    ]} 
                                                />
                                                <View style={s.contentWrapper}>
                                                    {info.materia.nrc && (
                                                        <Text style={s.materiaGrupo}>
                                                            NRC: {info.materia.nrc}
                                                        </Text>
                                                    )}
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
                                                </View>
                                            </>
                                        )}
                                    </View>
                                )
                            })}
                        </View>
                    ))}

                    {/* Referencia de materias en la misma hoja */}
                    <Text style={s.refTitulo}>Referencia de materias</Text>
                    <View style={s.refGrid}>
                        {materiasConColor.map(({ materia, color }, i) => (
                            <View key={`${materia.nrc}-${materia.grupo}-${i}`} style={s.refCard}>
                                <View
                                    style={[
                                        s.refColorBar,
                                        { backgroundColor: colorHex(color) },
                                    ]}
                                />
                                <View style={{ flex: 1 }}>
                                    <Text style={s.refMateria}>{materia.nombre}</Text>
                                    <Text style={s.refNrc}>NRC: {materia.nrc ?? "-"}</Text>
                                    {(materia.horarios ?? []).map((h, j) => (
                                        <View key={j} style={s.refSlot}>
                                            <Text>
                                                {diaCorto(h.dia, diasNombres)}{" "}
                                                {(h.hora_inicio || "").substring(0, 5)}-
                                                {(h.hora_fin || "").substring(0, 5)}
                                            </Text>
                                            <Text style={s.refSalon}>{h.aula ?? "-"}</Text>
                                        </View>
                                    ))}
                                </View>
                            </View>
                        ))}
                    </View>
                </Page>
            ) : (
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
                    <Text style={s.refTitulo}>Referencia de materias</Text>
                    <View style={s.refGrid}>
                        {materiasConColor.map(({ materia, color }, i) => (
                            <View key={`${materia.nrc}-${materia.grupo}-${i}`} style={s.refCard}>
                                <View
                                    style={[
                                        s.refColorBar,
                                        { backgroundColor: colorHex(color) },
                                    ]}
                                />
                                <View style={{ flex: 1 }}>
                                    <Text style={s.refMateria}>{materia.nombre}</Text>
                                    <Text style={s.refNrc}>NRC: {materia.nrc ?? "-"}</Text>
                                    {(materia.horarios ?? []).map((h, j) => (
                                        <View key={j} style={s.refSlot}>
                                            <Text>
                                                {diaCorto(h.dia, diasNombres)}{" "}
                                                {(h.hora_inicio || "").substring(0, 5)}-
                                                {(h.hora_fin || "").substring(0, 5)}
                                            </Text>
                                            <Text style={s.refSalon}>{h.aula ?? "-"}</Text>
                                        </View>
                                    ))}
                                </View>
                            </View>
                        ))}
                    </View>
                </Page>
            )}
        </Document>
    )
}
