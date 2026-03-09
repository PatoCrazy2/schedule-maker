import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ChevronDown, ChevronRight } from "lucide-react"
import { listProfessors, getProfessorReviews } from "@/api/professors"
import { StarRating } from "@/components/StarRating"
import { clasificarPromedio } from "@/lib/evaluacion"
import { diasToNombres } from "@/lib/dias"
import type { ProfessorListItem, ProfessorRatingResponse } from "@/types/api"

function formatHorario(
  dia: string,
  hi: string,
  hf: string,
  aula?: string
) {
  const d = diasToNombres(dia)
  return aula ? `${d} ${hi}-${hf} (${aula})` : `${d} ${hi}-${hf}`
}

export function VerProfesoresPage() {
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data: professors, isLoading } = useQuery({
    queryKey: ["professors-list"],
    queryFn: listProfessors,
  })

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-center text-muted-foreground">Cargando...</p>
      </div>
    )
  }

  if (!professors?.length) {
    return (
      <div className="p-6">
        <h2 className="mb-4 text-xl font-semibold">Ver profesores</h2>
        <p className="rounded-lg border bg-muted/30 p-6 text-center text-muted-foreground">
          No hay profesores registrados. Sube un PDF de oferta para cargar datos.
        </p>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h2 className="mb-4 text-xl font-semibold">Ver profesores</h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Lista de profesores, materias con NRC y evaluaciones por materia
      </p>

      <div className="space-y-2">
        {professors.map((p) => (
          <div key={p.name} className="overflow-hidden rounded-lg border">
            <button
              type="button"
              onClick={() => setExpanded(expanded === p.name ? null : p.name)}
              className="flex w-full items-center justify-between p-4 text-left hover:bg-muted/50"
            >
              <div className="flex items-center gap-2">
                {expanded === p.name ? (
                  <ChevronDown size={18} />
                ) : (
                  <ChevronRight size={18} />
                )}
                <span className="font-medium">{p.name}</span>
                {p.total_reviews > 0 && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <StarRating rating={p.average_rating} size={14} />
                    {p.average_rating} - {clasificarPromedio(p.average_rating)}{" "}
                    ({p.total_reviews} evaluacion{p.total_reviews !== 1 ? "es" : ""})
                  </span>
                )}
              </div>
              <span className="text-xs text-muted-foreground">
                {p.courses?.length ?? p.materias.length} materia
                {(p.courses?.length ?? p.materias.length) !== 1 ? "s" : ""}
              </span>
            </button>

            {expanded === p.name && (
              <ProfessorDetail professor={p} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function ProfessorDetail({ professor }: { professor: ProfessorListItem }) {
  const { data: reviewsData } = useQuery({
    queryKey: ["professor-reviews", professor.name],
    queryFn: () => getProfessorReviews(professor.name),
  })

  const courses = professor.courses ?? professor.materias.map((m) => ({
    nrc: "",
    clave: "",
    nombre: m,
    grupo: "",
    horarios: [],
  }))

  const reviewsByMateria = (reviewsData?.reviews ?? []).reduce(
    (acc, r) => {
      const key = r.materia_nombre ?? "General"
      if (!acc[key]) acc[key] = []
      acc[key].push(r)
      return acc
    },
    {} as Record<string, ProfessorRatingResponse["reviews"]>
  )

  
  return (
    <div className="border-t bg-muted/20 p-4">
      <div className="space-y-4">
        {courses.map((c, i) => {
          const key = c.nrc ? `${c.nrc}-${c.grupo}` : `${c.nombre}-${i}`
          const materiaReviews = reviewsByMateria[c.nombre] ?? []
          return (
            <div
              key={key}
              className="rounded-lg border bg-background p-4"
            >
              <div className="mb-2 flex items-baseline gap-2">
                <h4 className="font-medium">{c.nombre}</h4>
                {c.nrc && (
                  <span className="text-xs text-muted-foreground">
                    NRC {c.nrc} | {c.clave} | Grupo {c.grupo}
                  </span>
                )}
              </div>
              {c.horarios?.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  {c.horarios.map((h, j) => (
                    <span key={j} className="rounded bg-muted px-2 py-0.5">
                      {formatHorario(h.dia, h.hora_inicio, h.hora_fin, h.aula)}
                    </span>
                  ))}
                </div>
              )}
              {materiaReviews.length > 0 ? (
                <div className="space-y-2">
                  {materiaReviews.map((r) => (
                    <ReviewCard key={r.id} review={r} />
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">
                  Sin evaluacion para esta materia
                </p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ReviewCard({
  review,
}: {
  review: ProfessorRatingResponse["reviews"][0]
}) {
  const prom = review.promedio ?? review.rating
  const metricas = [
    review.dominio_contenido && "Dominio",
    review.claridad && "Claridad",
    review.metodologia && "Metodologia",
    review.justicia_evaluacion && "Justicia",
    review.exigencia && "Exigencia",
    review.apoyo && "Apoyo",
    review.organizacion && "Organizacion",
    review.impacto && "Impacto",
  ].filter(Boolean)

  return (
    <div className="rounded border bg-muted/20 p-3 text-sm">
      <div className="mb-2 flex items-center gap-2">
        {prom != null && <StarRating rating={prom} size={14} />}
        <span className="text-xs text-muted-foreground">
          {new Date(review.created_at).toLocaleDateString()}
        </span>
      </div>
      {metricas.length > 0 && (
        <div className="mb-2 text-xs text-muted-foreground">
          {metricas.join(", ")}
        </div>
      )}
      {review.comentario_general && (
        <p className="text-xs">{review.comentario_general}</p>
      )}
    </div>
  )
}
