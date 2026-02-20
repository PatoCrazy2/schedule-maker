import { useScheduleStore } from "@/store/scheduleStore"
import { diasToNombres } from "@/lib/dias"
import { Download } from "lucide-react"
import { api } from "@/api/client"

function formatHorario(
  dia: string,
  horaInicio: string,
  horaFin: string,
  aula?: string
) {
  const nombre = diasToNombres(dia)
  const hora = [horaInicio, horaFin].filter(Boolean).join("-")
  return aula ? `${nombre} ${hora} (${aula})` : `${nombre} ${hora}`
}

export function HomePage() {
  const { selectedSchedule } = useScheduleStore()

  const handleExportIcs = async () => {
    if (!selectedSchedule?.materias?.length) return
    try {
      const { data } = await api.post(
        "/api/export/ics",
        { materias: selectedSchedule.materias },
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

  if (!selectedSchedule?.materias?.length) {
    return (
      <div className="p-6">
        <h2 className="mb-4 text-xl font-semibold">Tu horario</h2>
        <p className="rounded-lg border bg-muted/30 p-6 text-center text-muted-foreground">
          No hay horario creado. Ve a Crear horario para seleccionar materias y
          generar tu calendario.
        </p>
      </div>
    )
  }

  const materias = selectedSchedule.materias

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Tu horario</h2>
        <div className="flex gap-2">
          <a
            href="https://calendar.google.com"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm hover:bg-muted"
          >
            Google Calendar
          </a>
          <button
            onClick={handleExportIcs}
            className="flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Download size={16} />
            Exportar .ics
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {materias.map((m, i) => (
          <div
            key={`${m.nrc}-${m.grupo}-${i}`}
            className="rounded-lg border bg-card p-4"
          >
            <h3 className="font-medium">
              {m.nombre}
              {m.clave && (
                <span className="ml-2 text-sm text-muted-foreground">
                  {m.clave} - {m.grupo ?? "?"}
                </span>
              )}
            </h3>
            {m.profesor && (
              <p className="text-sm text-muted-foreground">{m.profesor}</p>
            )}
            <div className="mt-2 flex flex-wrap gap-2 text-sm">
              {m.horarios?.map((h, j) => (
                <span
                  key={j}
                  className="rounded bg-muted px-2 py-1"
                >
                  {formatHorario(h.dia, h.hora_inicio, h.hora_fin, h.aula)}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
