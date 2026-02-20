import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { StarRating } from "./StarRating"
import { StarRatingInput } from "./StarRatingInput"
import { createProfessorReview, getProfessorRatingsBatch } from "@/api/professors"
import { METRICAS } from "@/lib/evaluacion"
import type { MateriaExtraida } from "@/types/api"
import { cn } from "@/lib/utils"

interface EvaluarMaestrosSectionProps {
  materias: MateriaExtraida[]
}

export function EvaluarMaestrosSection({ materias }: EvaluarMaestrosSectionProps) {
  const [selectedProfessor, setSelectedProfessor] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const professorNames = [
    ...new Set(materias.map((m) => m.profesor).filter(Boolean)),
  ] as string[]

  const { data: ratings } = useQuery({
    queryKey: ["professor-ratings", ...professorNames.sort()],
    queryFn: () => getProfessorRatingsBatch(professorNames),
    enabled: professorNames.length > 0,
  })

  if (professorNames.length === 0) return null

  return (
    <section className="rounded-lg border bg-card p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold">
        Instrumento de evaluacion docente (Escala 1-5)
      </h3>
      <p className="mb-4 text-xs text-muted-foreground">
        1=Muy deficiente, 2=Deficiente, 3=Aceptable, 4=Bueno, 5=Excelente
      </p>

      <div className="space-y-2">
        {professorNames.map((name) => (
          <div
            key={name}
            className={cn(
              "flex items-center justify-between rounded-lg border p-3",
              selectedProfessor === name && "border-primary bg-primary/5"
            )}
          >
            <div className="flex items-center gap-3">
              <span className="font-medium">{name}</span>
              {ratings?.[name]?.total_reviews ? (
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <StarRating rating={ratings[name].average_rating} size={12} />
                  {ratings[name].average_rating} ({ratings[name].total_reviews})
                </span>
              ) : (
                <span className="text-xs text-muted-foreground">Sin evaluaciones</span>
              )}
            </div>
            <button
              type="button"
              onClick={() => {
                setSelectedProfessor(selectedProfessor === name ? null : name)
              }}
              className="rounded border px-3 py-1 text-xs hover:bg-muted"
            >
              {selectedProfessor === name ? "Cerrar" : "Evaluar"}
            </button>
          </div>
        ))}
      </div>

      {selectedProfessor && (
        <ReviewForm
          professorName={selectedProfessor}
          materias={materias.filter((m) => m.profesor === selectedProfessor)}
          onClose={() => setSelectedProfessor(null)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["professor-ratings"] })
            queryClient.invalidateQueries({ queryKey: ["professor-reviews"] })
            queryClient.invalidateQueries({ queryKey: ["professors-list"] })
          }}
        />
      )}
    </section>
  )
}

interface ReviewFormProps {
  professorName: string
  materias: MateriaExtraida[]
  onClose: () => void
  onSuccess: () => void
}

function ReviewForm({
  professorName,
  materias,
  onClose,
  onSuccess,
}: ReviewFormProps) {
  const [materiaNombre, setMateriaNombre] = useState("")
  const [values, setValues] = useState<Record<string, number>>({})
  const [justificaciones, setJustificaciones] = useState<Record<string, string>>({})
  const [comentarioGeneral, setComentarioGeneral] = useState("")

  const mutation = useMutation({
    mutationFn: createProfessorReview,
    onSuccess: () => {
      setValues({})
      setJustificaciones({})
      setComentarioGeneral("")
      setMateriaNombre("")
      onSuccess()
    },
  })

  const metricasConValor = METRICAS.filter((m) => (values[m.key] ?? 0) >= 1)
  const puedeEnviar = metricasConValor.length >= 1

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!puedeEnviar) return

    const body: Record<string, unknown> = {
      professor_name: professorName,
      materia_nombre: materiaNombre || undefined,
      comentario_general: comentarioGeneral.trim() || undefined,
    }
    METRICAS.forEach((m) => {
      const v = values[m.key]
      if (v >= 1) body[m.key] = v
      const j = justificaciones[m.justificacionKey]
      if (j?.trim()) body[m.justificacionKey] = j.trim()
    })

    mutation.mutate(body as unknown as Parameters<typeof createProfessorReview>[0])
  }

  const materiasDelProf = [...new Set(materias.map((m) => m.nombre).filter(Boolean))]

  return (
    <form onSubmit={handleSubmit} className="mt-4 space-y-4 border-t pt-4">
      <h4 className="text-sm font-medium">{professorName}</h4>

      {materiasDelProf.length > 0 && (
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Materia (opcional)
          </label>
          <select
            value={materiaNombre}
            onChange={(e) => setMateriaNombre(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm"
          >
            <option value="">-- Seleccionar --</option>
            {materiasDelProf.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="space-y-4">
        {METRICAS.map((m) => (
          <div key={m.key} className="rounded border p-3">
            <p className="mb-2 text-xs font-medium">{m.label}</p>
            <p className="mb-2 text-xs text-muted-foreground">{m.pregunta}</p>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs">Escala 1-5</span>
              <StarRatingInput
                value={values[m.key] ?? 0}
                onChange={(v) => setValues((prev) => ({ ...prev, [m.key]: v }))}
                size={18}
              />
            </div>
            <textarea
              placeholder="Por que asignaste esta calificacion? (opcional)"
              value={justificaciones[m.justificacionKey] ?? ""}
              onChange={(e) =>
                setJustificaciones((prev) => ({
                  ...prev,
                  [m.justificacionKey]: e.target.value,
                }))
              }
              className="w-full rounded border px-2 py-1 text-xs"
              rows={2}
              maxLength={1000}
            />
          </div>
        ))}
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium">
          Comentario general (fortalezas, areas de mejora, recomendaciones)
        </label>
        <textarea
          value={comentarioGeneral}
          onChange={(e) => setComentarioGeneral(e.target.value)}
          placeholder="Fortalezas, areas de mejora, recomendaciones..."
          className="w-full rounded border px-3 py-2 text-sm"
          rows={3}
          maxLength={2000}
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!puedeEnviar || mutation.isPending}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {mutation.isPending ? "Enviando..." : "Enviar evaluacion"}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border px-4 py-2 text-sm hover:bg-muted"
        >
          Cerrar
        </button>
      </div>

      {mutation.isError && (
        <p className="text-sm text-destructive">Error al enviar. Intenta de nuevo.</p>
      )}
    </form>
  )
}
