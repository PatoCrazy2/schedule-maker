import { useMemo, useState, useEffect } from "react"
import { pdf } from "@react-pdf/renderer"
import { useOfertaStore } from "@/store/ofertaStore"
import { useScheduleStore } from "@/store/scheduleStore"
import { diasToNombres } from "@/lib/dias"
import { Download, Loader2, FileText } from "lucide-react"
import { api } from "@/api/client"
import { cn } from "@/lib/utils"
import { canAddMateria } from "@/lib/schedule"
import type { SubjectResponse, CourseResponse, MateriaExtraida } from "@/types/api"
import { HorarioDocument } from "@/components/HorarioDocument"

// ─── Constantes globales ──────────────────────────────────────────────────────
const DIAS_ORDEN = ["L", "A", "M", "J", "V", "S"]

const COLORES_TAILWIND = [
  "bg-blue-200",
  "bg-green-200",
  "bg-amber-200",
  "bg-purple-200",
  "bg-rose-200",
  "bg-cyan-200",
]

function formatHorario(dia: string, hi: string, hf: string, aula?: string) {
  const d = diasToNombres(dia)
  return aula ? `${d} ${hi}-${hf} (${aula})` : `${d} ${hi}-${hf}`
}

// ─── Componente ───────────────────────────────────────────────────────────────
export function CrearHorarioPage() {
  const { oferta } = useOfertaStore()
  const {
    selectedMaterias,
    selectedSchedule,
    setSelectedSchedule,
    toggleMateria,
    clearSchedule,
  } = useScheduleStore()

  const [showCalendar, setShowCalendar] = useState(true)

  // Estados Read Layer
  const [subjects, setSubjects] = useState<SubjectResponse[]>([])
  const [selectedSubject, setSelectedSubject] = useState<string>("")
  const [coursesLoading, setCoursesLoading] = useState(false)
  const [coursesOptions, setCoursesOptions] = useState<CourseResponse[]>([])

  const [isExporting, setIsExporting] = useState(false)

  // ── Cargar materias disponibles ──────────────────────────────────────────
  useEffect(() => {
    async function loadSubjects() {
      if (!oferta?.file_hash) return
      try {
        const { data } = await api.get<SubjectResponse[]>(
          `/api/v1/files/${oferta.file_hash}/subjects`
        )
        setSubjects(data)
      } catch (err) {
        console.error("Error al cargar las materias del archivo", err)
      }
    }
    loadSubjects()
  }, [oferta?.file_hash])

  // ── Cargar grupos/cursos al seleccionar materia ──────────────────────────
  useEffect(() => {
    async function loadCourses() {
      if (!oferta?.file_hash || !selectedSubject) {
        setCoursesOptions([])
        return
      }
      try {
        setCoursesLoading(true)
        const { data } = await api.get<CourseResponse[]>(
          `/api/v1/files/${oferta.file_hash}/courses`,
          { params: { subject_name: selectedSubject } }
        )
        setCoursesOptions(data)
      } catch (err) {
        console.error("Error al cargar los grupos/cursos", err)
      } finally {
        setCoursesLoading(false)
      }
    }
    loadCourses()
  }, [oferta?.file_hash, selectedSubject])

  // ── Exportar ICS ─────────────────────────────────────────────────────────
  const handleExportIcs = async () => {
    const materias = selectedSchedule?.materias ?? selectedMaterias
    if (!materias.length) return
    try {
      const { data } = await api.post(
        "/api/export/ics",
        { materias },
        { responseType: "blob" }
      )
      const url = URL.createObjectURL(new Blob([data]))
      const a = document.createElement("a")
      a.href = url
      a.download = "horario.ics"
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      console.error("Error exportando ICS")
    }
  }

  // ── Colores por materia ───────────────────────────────────────────────────
  const materiasConColor = useMemo(() => {
    const materias = selectedSchedule?.materias ?? selectedMaterias
    return materias.map((m, i) => ({
      materia: m,
      color: COLORES_TAILWIND[i % COLORES_TAILWIND.length],
    }))
  }, [selectedSchedule?.materias, selectedMaterias])

  // ── Horas dinámicas del calendario ─────────────────────────────────────────
  const horasVisibles = useMemo(() => {
    let minHora = 24
    let maxHora = 0
    let hasMaterias = false

    materiasConColor.forEach(({ materia }) => {
      ; (materia.horarios ?? []).forEach((s) => {
        hasMaterias = true
        const [hiH] = (s.hora_inicio || "00:00").split(":")
        const [hfH, hfM] = (s.hora_fin || "00:00").split(":")

        const hiNum = parseInt(hiH || "0", 10)
        const hfNumRaw = parseInt(hfH || "0", 10)
        const hfMin = parseInt(hfM || "0", 10)
        const hfNum = hfMin > 0 ? hfNumRaw + 1 : hfNumRaw

        if (hiNum < minHora) minHora = hiNum
        if (hfNum > maxHora) maxHora = hfNum
      })
    })

    if (!hasMaterias) {
      return Array.from({ length: 9 }, (_, i) => 7 + i) // 7:00 a 15:00 por defecto
    }

    const start = Math.max(0, minHora)
    const end = Math.min(24, maxHora)

    return Array.from({ length: end - start }, (_, i) => start + i)
  }, [materiasConColor])

  // ── Generar y descargar PDF (vectorial via @react-pdf/renderer) ───────────
  const handleGenerarHorario = async () => {
    if (selectedMaterias.length === 0) return

    // Actualiza el store con el horario seleccionado
    setSelectedSchedule({ materias: selectedMaterias })

    const pdfWindow = window.open('', '_blank')
    if (pdfWindow) {
      pdfWindow.document.write('<html><head><title>Horario PDF</title></head><body style="font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh;"><h2>Generando documento...</h2></body></html>')
    }

    try {
      setIsExporting(true)

      const blob = await pdf(
        <HorarioDocument
          showCalendar={showCalendar}
          materiasConColor={materiasConColor}
          horas={horasVisibles}
          diasOrden={DIAS_ORDEN}
          diasNombres={diasToNombres}
          formatHorario={formatHorario}
          selectedMaterias={selectedMaterias}
        />
      ).toBlob()

      const url = URL.createObjectURL(blob)
      if (pdfWindow) {
        pdfWindow.location.href = url
      }
    } catch (error) {
      console.error("Error al exportar a PDF:", error)
      if (pdfWindow) {
        pdfWindow.close()
      }
    } finally {
      setIsExporting(false)
    }
  }

  // ── Guard: sin oferta ─────────────────────────────────────────────────────
  if (!oferta?.materias?.length) {
    return (
      <div className="p-6">
        <h2 className="mb-4 text-xl font-semibold">Crear horario</h2>
        <p className="rounded-lg border bg-muted/30 p-6 text-center text-muted-foreground">
          Sube un PDF en la sección Subir PDF para cargar materias y crear tu
          horario.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-semibold">Crear horario</h2>

      {/* ── Selectores de materia / grupo ──────────────────────────────── */}
      <div className="flex flex-col gap-4">
        <div>
          <label className="mb-2 block text-sm font-medium">Selecciona una Materia</label>
          <select
            className="w-full max-w-sm rounded-md border p-2 text-sm"
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
          >
            <option value="">-- Elige una materia --</option>
            {subjects.map((sub, idx) => (
              <option key={idx} value={sub.name}>
                {sub.name}
              </option>
            ))}
          </select>
        </div>

        {selectedSubject && (
          <div>
            <h3 className="mb-3 text-sm font-medium">
              Elige el grupo/horario
              {coursesLoading && (
                <Loader2 className="ml-2 inline h-4 w-4 animate-spin text-muted-foreground" />
              )}
            </h3>
            <div className="flex flex-wrap gap-2">
              {!coursesLoading && coursesOptions.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No se encontraron grupos para esta materia.
                </p>
              )}
              {coursesOptions.map((c, i) => {
                const isSelected = selectedMaterias.some(
                  (x) =>
                    (x.nrc ?? "") === (c.nrc ?? "") &&
                    (x.grupo ?? "") === (c.group_code ?? "")
                )

                const materiaFormat: MateriaExtraida = {
                  nrc: c.nrc,
                  nombre: c.subject_name,
                  clave: c.course_code,
                  grupo: c.group_code,
                  profesor: c.professor,
                  creditos: c.credits,
                  horarios: c.time_slots.map((ts) => ({
                    dia: ts.day,
                    hora_inicio: ts.start_time,
                    hora_fin: ts.end_time,
                    aula: ts.classroom,
                  })),
                }

                const checkAdd = isSelected
                  ? { allowed: true }
                  : canAddMateria(materiaFormat, selectedMaterias)

                return (
                  <button
                    key={`${c.nrc}-${i}`}
                    type="button"
                    onClick={() => toggleMateria(materiaFormat)}
                    disabled={!isSelected && !checkAdd.allowed}
                    title={
                      !checkAdd.allowed && !isSelected
                        ? checkAdd.reason
                        : undefined
                    }
                    className={cn(
                      "rounded-lg border px-3 py-2 text-left text-sm transition-colors max-w-[280px]",
                      isSelected
                        ? "border-primary bg-primary/10 text-primary"
                        : !checkAdd.allowed
                          ? "opacity-50 cursor-not-allowed bg-muted"
                          : "hover:bg-muted"
                    )}
                  >
                    <div className="font-medium">
                      NRC: {c.nrc} {c.professor && `(${c.professor})`}
                    </div>
                    {c.time_slots.length > 0 ? (
                      <div className="mt-1 text-xs text-muted-foreground">
                        {c.time_slots
                          .map((ts) =>
                            formatHorario(
                              ts.day,
                              ts.start_time.substring(0, 5),
                              ts.end_time.substring(0, 5),
                              ts.classroom
                            )
                          )
                          .join(" | ")}
                      </div>
                    ) : (
                      <div className="mt-1 text-xs text-muted-foreground">
                        Sin horario asignado
                      </div>
                    )}
                    {!checkAdd.allowed && !isSelected && (
                      <div className="mt-2 text-[10px] text-destructive font-semibold leading-tight">
                        {checkAdd.reason}
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* ── Botones de acción ───────────────────────────────────────────── */}
      <div className="flex gap-2 pt-4">
        <button
          onClick={handleGenerarHorario}
          disabled={selectedMaterias.length === 0 || isExporting}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <FileText size={16} />
          )}
          {isExporting ? "Generando..." : "Generar .pdf"}
        </button>
        <button
          onClick={() => clearSchedule()}
          className="rounded-lg border px-4 py-2 text-sm hover:bg-muted"
        >
          Limpiar
        </button>
        {(selectedSchedule?.materias?.length ?? selectedMaterias.length) > 0 && (
          <button
            onClick={handleExportIcs}
            className="flex items-center gap-2 rounded-lg border px-4 py-2 text-sm hover:bg-muted"
          >
            <Download size={16} />
            Exportar .ics
          </button>
        )}
      </div>

      {/* ── Vista previa del horario en pantalla ────────────────────────── */}
      {selectedMaterias.length > 0 && (
        <>
          {/* Toggle vista */}
          <div className="flex gap-2">
            <button
              onClick={() => setShowCalendar(true)}
              className={cn(
                "rounded px-3 py-1 text-sm",
                showCalendar ? "bg-primary text-primary-foreground" : "bg-muted"
              )}
            >
              Calendario
            </button>
            <button
              onClick={() => setShowCalendar(false)}
              className={cn(
                "rounded px-3 py-1 text-sm",
                !showCalendar ? "bg-primary text-primary-foreground" : "bg-muted"
              )}
            >
              Lista
            </button>
          </div>

          {/* Vista Calendario */}
          {showCalendar ? (
            <div className="overflow-x-auto rounded-lg border">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="min-w-[60px] px-2 py-2">Hora</th>
                    {DIAS_ORDEN.map((d) => (
                      <th key={d} className="min-w-[80px] px-2 py-2">
                        {diasToNombres(d)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {horasVisibles.map((hora) => (
                    <tr key={hora} className="border-b last:border-0">
                      <td className="px-2 py-1 font-medium">
                        {hora}:00 - {hora + 1}:00
                      </td>
                      {DIAS_ORDEN.map((dia) => {
                        let celdaInfo = null
                        for (const { materia, color } of materiasConColor) {
                          const slot = (materia.horarios ?? []).find((s) => {
                            const slotDia =
                              s.dia.length === 1 ? s.dia : s.dia[0]
                            const [hiH] = (s.hora_inicio || "00:00").split(":")
                            const [hfH, hfM] = (s.hora_fin || "00:00").split(":")
                            const hiNum = parseInt(hiH || "0", 10)
                            const hfNumRaw = parseInt(hfH || "0", 10)
                            const hfMin = parseInt(hfM || "0", 10)
                            const hfNum = hfMin > 0 ? hfNumRaw + 1 : hfNumRaw
                            return slotDia === dia && hora >= hiNum && hora < hfNum
                          })
                          if (slot) {
                            celdaInfo = { materia, color, slot }
                            break
                          }
                        }
                        return (
                          <td
                            key={dia}
                            className={cn(
                              "min-w-[80px] px-2 py-1 align-top border-x border-transparent",
                              celdaInfo && celdaInfo.color,
                              celdaInfo && "border-white/20"
                            )}
                          >
                            {celdaInfo && (
                              <div className="flex flex-col text-[10px] leading-[1.3] overflow-hidden">
                                <span
                                  className="font-bold line-clamp-2"
                                  title={celdaInfo.materia.nombre}
                                >
                                  {celdaInfo.materia.nombre}
                                </span>
                                <span className="font-medium opacity-80">
                                  Grp: {celdaInfo.materia.grupo}
                                </span>
                                {celdaInfo.slot.aula && (
                                  <span className="font-medium opacity-90 mt-0.5">
                                    Salon: {celdaInfo.slot.aula}
                                  </span>
                                )}
                              </div>
                            )}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            /* Vista Lista */
            <div className="space-y-3">
              {(selectedSchedule?.materias ?? selectedMaterias).map((m, i) => (
                <div
                  key={`${m.nrc}-${m.grupo}-${i}`}
                  className="rounded-lg border p-4"
                >
                  <h4 className="font-medium">
                    {m.nombre} - {m.clave} ({m.nrc})
                  </h4>
                  {m.profesor && (
                    <p className="text-sm text-muted-foreground">{m.profesor}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    {(m.horarios ?? []).map((h, j) => (
                      <span key={j} className="rounded bg-muted px-2 py-0.5">
                        {formatHorario(h.dia, h.hora_inicio, h.hora_fin, h.aula)}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
