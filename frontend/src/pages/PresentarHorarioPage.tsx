import { useState, useCallback, useEffect } from "react"
import { pdf } from "@react-pdf/renderer"
import { FileText, Loader2, Upload } from "lucide-react"
import { uploadHorarioAlumno } from "@/api/pdf"
import { diasToNombres } from "@/lib/dias"
import type { MateriaExtraida } from "@/types/api"
import { HorarioDocument } from "@/components/HorarioDocument"

const DIAS_ORDEN = ["L", "A", "M", "J", "V", "S"]

function horaToNum(h: string): number {
  const s = (h || "").trim()
  if (!s) return 0
  if (s.includes(":")) {
    const [hora] = s.split(":")
    return parseInt(hora || "0", 10)
  }
  if (s.length === 4 && /^\d{4}$/.test(s)) return parseInt(s.slice(0, 2), 10)
  return parseInt(s, 10) || 0
}
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
  const hiShort = (hi || "").substring(0, 5)
  const hfShort = (hf || "").substring(0, 5)
  return aula ? `${d} ${hiShort}-${hfShort} (${aula})` : `${d} ${hiShort}-${hfShort}`
}

export function PresentarHorarioPage() {
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [materias, setMaterias] = useState<MateriaExtraida[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [showCalendar, setShowCalendar] = useState(true)

  const materiasConColor = materias.map((m, i) => ({
    materia: m,
    color: COLORES_TAILWIND[i % COLORES_TAILWIND.length],
  }))

  const horasVisibles = (() => {
    let minHora = 24
    let maxHora = 0
    let hasMaterias = false
    materiasConColor.forEach(({ materia }) => {
      ;(materia.horarios ?? []).forEach((s) => {
        hasMaterias = true
        const hiNum = horaToNum(s.hora_inicio)
        const hfRaw = horaToNum(s.hora_fin)
        const hfNum = s.hora_fin?.match(/:59$|\d{4}$/) ? hfRaw + 1 : hfRaw
        if (hiNum < minHora) minHora = hiNum
        if (hfNum > maxHora) maxHora = hfNum
      })
    })
    if (!hasMaterias) return Array.from({ length: 9 }, (_, i) => 7 + i)
    const start = Math.max(0, minHora)
    const end = Math.min(24, maxHora)
    return Array.from({ length: end - start }, (_, i) => start + i)
  })()

  useEffect(() => {
    if (!pdfFile) return
    let cancelled = false
    setIsLoading(true)
    setError(null)
    uploadHorarioAlumno(pdfFile)
      .then((res) => {
        if (!cancelled) setMaterias(res.materias ?? [])
      })
      .catch((err) => {
        if (!cancelled) {
          setMaterias([])
          setError(err?.response?.data?.detail ?? "Error al procesar el PDF")
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [pdfFile])

  const handleExportPdf = useCallback(async () => {
    if (materias.length === 0) return
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
          selectedMaterias={materias}
        />
      ).toBlob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = "horario-presentado.pdf"
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error("Error exportando PDF:", err)
    } finally {
      setIsExporting(false)
    }
  }, [materias, materiasConColor, horasVisibles, showCalendar])

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div>
        <h2 className="text-xl font-semibold">Presentar horario</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Carga el PDF de tu horario de cursos inscritos. Se extraen las materias
          directamente y se muestra en formato legible como en Crear horario.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-muted/5 p-4 sm:p-6">
        <label className="mb-2 block text-sm font-medium">Cargar PDF</label>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-primary bg-primary/10 px-4 py-2 text-sm font-medium hover:bg-primary/20">
            <Upload size={18} />
            Seleccionar PDF
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f?.name.toLowerCase().endsWith(".pdf")) {
                  setPdfFile(f)
                }
              }}
            />
          </label>
          {pdfFile && (
            <span className="text-sm text-muted-foreground">{pdfFile.name}</span>
          )}
          {pdfFile && (
            <button
              type="button"
              onClick={() => {
                setPdfFile(null)
                setMaterias([])
                setError(null)
              }}
              className="text-sm text-muted-foreground hover:underline"
            >
              Quitar
            </button>
          )}
        </div>
        {isLoading && (
          <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Procesando PDF...
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {materias.length > 0 && (
        <div className="rounded-xl border border-border bg-muted/5 p-4 sm:p-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold">
              Vista previa ({materias.length} materias)
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowCalendar(true)}
                className={`rounded px-3 py-1 text-sm ${
                  showCalendar ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}
              >
                Calendario
              </button>
              <button
                onClick={() => setShowCalendar(false)}
                className={`rounded px-3 py-1 text-sm ${
                  !showCalendar ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}
              >
                Lista
              </button>
              <button
                onClick={handleExportPdf}
                disabled={isExporting}
                className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {isExporting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText size={16} />
                )}
                {isExporting ? "Generando..." : "Exportar PDF"}
              </button>
            </div>
          </div>

          {showCalendar ? (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="min-w-[60px] px-3 py-2.5">Hora</th>
                    {DIAS_ORDEN.map((d) => (
                      <th key={d} className="min-w-[80px] px-3 py-2.5">
                        {diasToNombres(d)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {horasVisibles.map((hora) => (
                    <tr key={hora} className="border-b last:border-0">
                      <td className="px-3 py-2 font-medium">
                        {hora}:00 - {hora + 1}:00
                      </td>
                      {DIAS_ORDEN.map((dia) => {
                        let celdaInfo: {
                          materia: MateriaExtraida
                          color: string
                          slot: { aula?: string }
                        } | null = null
                        for (const { materia, color } of materiasConColor) {
                          const slot = (materia.horarios ?? []).find((s) => {
                            const slotDia = (typeof s.dia === "string" ? s.dia : s.dia?.[0]) || ""
                            const hiNum = horaToNum(s.hora_inicio)
                            const hfRaw = horaToNum(s.hora_fin)
                            const hfNum = s.hora_fin?.match(/:59$|\d{4}$/)
                              ? hfRaw + 1
                              : hfRaw
                            return (
                              slotDia === dia && hora >= hiNum && hora < hfNum
                            )
                          })
                          if (slot) {
                            celdaInfo = { materia, color, slot }
                            break
                          }
                        }
                        return (
                          <td
                            key={dia}
                            className={`min-w-[80px] px-3 py-2 align-top border-x border-transparent ${
                              celdaInfo ? celdaInfo.color + " border-white/20" : ""
                            }`}
                          >
                            {celdaInfo && (
                              <div className="flex flex-col gap-0.5 text-[10px] leading-[1.3] overflow-hidden">
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
            <div className="space-y-4">
              {materiasConColor.map(({ materia, color }, i) => (
                <div
                  key={`${materia.nrc}-${materia.grupo}-${i}`}
                  className="flex gap-4 overflow-hidden rounded-xl border border-border bg-card shadow-sm"
                >
                  <div className={`w-2 shrink-0 ${color}`} />
                  <div className="flex-1 py-4 pr-4">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <h4 className="font-semibold text-foreground">{materia.nombre}</h4>
                      <span className="text-xs text-muted-foreground">
                        {materia.clave}  ·  Grp {materia.grupo}
                      </span>
                    </div>
                    <div className="mt-1 font-mono text-sm tabular-nums">
                      NRC: {materia.nrc ?? "-"}
                    </div>
                    {materia.profesor && (
                      <p className="mt-1 text-sm text-muted-foreground">
                        {materia.profesor}
                      </p>
                    )}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(materia.horarios ?? []).map((h, j) => (
                        <span
                          key={j}
                          className="flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-2.5 py-1.5 text-xs"
                        >
                          {diasToNombres(h.dia)}{" "}
                          {(h.hora_inicio || "").substring(0, 5)}-
                          {(h.hora_fin || "").substring(0, 5)}
                          {h.aula && (
                            <span className="font-semibold">{h.aula}</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 rounded-lg border border-border bg-muted/20 p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Referencia de materias
            </p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {materiasConColor.map(({ materia, color }, i) => (
                <div
                  key={`${materia.nrc}-${i}`}
                  className="flex gap-3 rounded-lg border border-border bg-background p-3"
                >
                  <div
                    className={`h-14 w-4 shrink-0 rounded ${color}`}
                    title={materia.nombre}
                  />
                  <div className="min-w-0 flex-1 text-xs">
                    <div className="font-semibold">{materia.nombre}</div>
                    <div className="mt-1 font-medium tabular-nums">
                      NRC: {materia.nrc ?? "-"}
                    </div>
                    <div className="mt-2 space-y-1">
                      {(materia.horarios ?? []).map((h, j) => (
                        <div
                          key={j}
                          className="flex justify-between gap-2 rounded bg-muted/60 px-2 py-1"
                        >
                          <span className="text-[10px] text-muted-foreground">
                            {diasToNombres(h.dia).slice(0, 3)}{" "}
                            {(h.hora_inicio || "").substring(0, 5)}-
                            {(h.hora_fin || "").substring(0, 5)}
                          </span>
                          <span className="font-semibold tabular-nums">
                            {h.aula ?? "-"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
