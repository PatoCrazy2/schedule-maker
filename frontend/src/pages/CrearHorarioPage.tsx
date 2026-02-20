import { useMemo, useState } from "react"
import { useOfertaStore } from "@/store/ofertaStore"
import { useScheduleStore } from "@/store/scheduleStore"
import { diasToNombres } from "@/lib/dias"
import { Download } from "lucide-react"
import { api } from "@/api/client"
import { cn } from "@/lib/utils"

const DIAS_ORDEN = ["L", "A", "M", "J", "V", "S"]
const HORAS = Array.from({ length: 16 }, (_, i) => 7 + i)

function formatHorario(dia: string, hi: string, hf: string, aula?: string) {
  const d = diasToNombres(dia)
  return aula ? `${d} ${hi}-${hf} (${aula})` : `${d} ${hi}-${hf}`
}

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

  const handleGenerarHorario = () => {
    if (selectedMaterias.length === 0) return
    setSelectedSchedule({ materias: selectedMaterias })
  }

  const celdasOcupadas = useMemo(() => {
    const ocupadas = new Set<string>()
    const materias = selectedSchedule?.materias ?? selectedMaterias
    for (const m of materias) {
      for (const h of m.horarios ?? []) {
        const dia = h.dia.length === 1 ? h.dia : h.dia[0]
        const [hi] = (h.hora_inicio || "00:00").split(":")
        const [hf] = (h.hora_fin || "00:00").split(":")
        const hiNum = parseInt(hi || "0", 10)
        const hfNum = parseInt(hf || "0", 10)
        for (let hora = hiNum; hora < hfNum; hora++) {
          ocupadas.add(`${dia}-${hora}`)
        }
      }
    }
    return ocupadas
  }, [selectedSchedule?.materias, selectedMaterias])

  const materiasConColor = useMemo(() => {
    const colores = [
      "bg-blue-200",
      "bg-green-200",
      "bg-amber-200",
      "bg-purple-200",
      "bg-rose-200",
      "bg-cyan-200",
    ]
    const materias = selectedSchedule?.materias ?? selectedMaterias
    return materias.map((m, i) => ({
      materia: m,
      color: colores[i % colores.length],
    }))
  }, [selectedSchedule?.materias, selectedMaterias])

  if (!oferta?.materias?.length) {
    return (
      <div className="p-6">
        <h2 className="mb-4 text-xl font-semibold">Crear horario</h2>
        <p className="rounded-lg border bg-muted/30 p-6 text-center text-muted-foreground">
          Sube un PDF en la seccion Subir PDF para cargar materias y crear tu
          horario.
        </p>
      </div>
    )
  }

  const materias = oferta.materias

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-semibold">Crear horario</h2>

      <div>
        <h3 className="mb-3 text-sm font-medium">
          Selecciona las materias para tu horario
        </h3>
        <div className="flex flex-wrap gap-2">
          {materias.map((m, i) => {
            const key = `${m.nrc ?? ""}-${m.grupo ?? ""}-${i}`
            const isSelected = selectedMaterias.some(
              (x) =>
                (x.nrc ?? "") === (m.nrc ?? "") &&
                (x.grupo ?? "") === (m.grupo ?? "")
            )
            return (
              <button
                key={key}
                type="button"
                onClick={() => toggleMateria(m)}
                className={cn(
                  "rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                  isSelected
                    ? "border-primary bg-primary/10 text-primary"
                    : "hover:bg-muted"
                )}
              >
                {m.nombre}
                {m.grupo && (
                  <span className="ml-1 text-muted-foreground">({m.grupo})</span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleGenerarHorario}
          disabled={selectedMaterias.length === 0}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          Generar horario
        </button>
        <button
          onClick={() => {
            clearSchedule()
          }}
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

      {selectedMaterias.length > 0 && (
        <>
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
                  {HORAS.map((hora) => (
                    <tr key={hora} className="border-b last:border-0">
                      <td className="px-2 py-1 font-medium">
                        {hora}:00 - {hora + 1}:00
                      </td>
                      {DIAS_ORDEN.map((dia) => {
                        const ocupada = celdasOcupadas.has(`${dia}-${hora}`)
                        const materiaEnCelda = materiasConColor.find(({ materia }) =>
                          (materia.horarios ?? []).some((slot) => {
                            const slotDia =
                              slot.dia.length === 1 ? slot.dia : slot.dia[0]
                            const [hi] = (slot.hora_inicio || "00:00").split(":")
                            const slotHora = parseInt(hi || "0", 10)
                            return slotDia === dia && slotHora === hora
                          })
                        )
                        return (
                          <td
                            key={dia}
                            className={cn(
                              "min-w-[80px] px-2 py-1",
                              ocupada && materiaEnCelda && materiaEnCelda.color
                            )}
                          >
                            {materiaEnCelda && (
                              <span className="truncate text-[10px]">
                                {materiaEnCelda.materia.nombre} (
                                {materiaEnCelda.materia.grupo})
                              </span>
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
            <div className="space-y-3">
              {(selectedSchedule?.materias ?? selectedMaterias).map((m, i) => (
                <div
                  key={`${m.nrc}-${m.grupo}-${i}`}
                  className="rounded-lg border p-4"
                >
                  <h4 className="font-medium">
                    {m.nombre} - {m.clave} ({m.grupo})
                  </h4>
                  {m.profesor && (
                    <p className="text-sm text-muted-foreground">{m.profesor}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    {(m.horarios ?? []).map((h, j) => (
                      <span
                        key={j}
                        className="rounded bg-muted px-2 py-0.5"
                      >
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
