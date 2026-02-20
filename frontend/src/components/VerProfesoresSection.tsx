import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ChevronDown, ChevronRight } from "lucide-react"
import { listProfessors, getProfessorReviews } from "@/api/professors"
import { StarRating } from "./StarRating"
import { clasificarPromedio } from "@/lib/evaluacion"
import type { ProfessorRatingResponse } from "@/types/api"

export function VerProfesoresSection() {
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data: professors, isLoading } = useQuery({
    queryKey: ["professors-list"],
    queryFn: listProfessors,
  })

  if (isLoading) {
    return <p className="py-8 text-center text-muted-foreground">Cargando...</p>
  }

  if (!professors?.length) {
    return (
      <p className="py-8 text-center text-muted-foreground">
        No hay profesores registrados. Sube un PDF de oferta para cargar datos.
      </p>
    )
  }

  return (
    <section className="rounded-lg border bg-card p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold">Ver profesores</h3>
      <p className="mb-4 text-xs text-muted-foreground">
        Lista de profesores, materias registradas y evaluaciones
      </p>

      <div className="space-y-2">
        {professors.map((p) => (
          <div
            key={p.name}
            className="rounded-lg border overflow-hidden"
          >
            <button
              type="button"
              onClick={() =>
                setExpanded(expanded === p.name ? null : p.name)
              }
              className="flex w-full items-center justify-between p-3 text-left hover:bg-muted/50"
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
                    {p.average_rating} ({p.total_reviews})
                  </span>
                )}
              </div>
              <span className="text-xs text-muted-foreground">
                {p.materias.length} materia{p.materias.length !== 1 ? "s" : ""}
              </span>
            </button>

            {expanded === p.name && (
              <ProfessorDetail professorName={p.name} />
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

function ProfessorDetail({ professorName }: { professorName: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["professor-reviews", professorName],
    queryFn: () => getProfessorReviews(professorName),
  })

  if (isLoading) {
    return (
      <div className="border-t p-4 text-sm text-muted-foreground">
        Cargando evaluaciones...
      </div>
    )
  }

  if (!data || data.reviews.length === 0) {
    return (
      <div className="border-t p-4 text-sm text-muted-foreground">
        Sin evaluaciones aun
      </div>
    )
  }

  return (
    <div className="border-t bg-muted/20 p-4">
      <div className="mb-3 flex items-center gap-2">
        <StarRating rating={data.average_rating} size={18} />
        <span className="text-sm font-medium">
          {data.average_rating} - {clasificarPromedio(data.average_rating)}
        </span>
        <span className="text-xs text-muted-foreground">
          ({data.total_reviews} evaluacion{data.total_reviews !== 1 ? "es" : ""})
        </span>
      </div>
      <ul className="space-y-3">
        {data.reviews.map((r) => (
          <ReviewCard key={r.id} review={r} />
        ))}
      </ul>
    </div>
  )
}

function ReviewCard({ review }: { review: ProfessorRatingResponse["reviews"][0] }) {
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
    <li className="rounded border bg-background p-3 text-sm">
      <div className="mb-2 flex items-center gap-2">
        {prom != null && (
          <StarRating rating={prom} size={14} />
        )}
        <span className="text-xs text-muted-foreground">
          {new Date(review.created_at).toLocaleDateString()}
          {review.materia_nombre && ` - ${review.materia_nombre}`}
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
    </li>
  )
}
