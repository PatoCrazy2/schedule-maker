import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { X } from "lucide-react"
import { createProfessorReview, getProfessorReviews } from "@/api/professors"
import { clasificarPromedio } from "@/lib/evaluacion"
import { StarRating } from "./StarRating"
import { StarRatingInput } from "./StarRatingInput"
import type { ProfessorRatingResponse } from "@/types/api"
interface ProfessorReviewModalProps {
  professorName: string
  onClose: () => void
}

export function ProfessorReviewModal({ professorName, onClose }: ProfessorReviewModalProps) {
  const queryClient = useQueryClient()
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["professor-reviews", professorName],
    queryFn: () => getProfessorReviews(professorName),
  })

  const createMutation = useMutation({
    mutationFn: createProfessorReview,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["professor-reviews", professorName] })
      queryClient.invalidateQueries({ queryKey: ["professor-ratings"] })
      setRating(0)
      setComment("")
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (rating < 1 || rating > 5) return
    createMutation.mutate({
      professor_name: professorName,
      rating,
      comment: comment.trim() || undefined,
    })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-background p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Reseñas: {professorName}</h3>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-muted"
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
        </div>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Cargando reseñas...</p>
        ) : (
          <>
            <RatingSummary data={data} />

            <form onSubmit={handleSubmit} className="mt-6 space-y-3 border-t pt-4">
              <p className="text-sm font-medium">Evaluacion rapida (1-5)</p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Calificacion general *</span>
                <StarRatingInput value={rating} onChange={setRating} />
              </div>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Comentario (opcional)"
                className="w-full rounded border px-3 py-2 text-sm"
                rows={3}
                maxLength={2000}
              />
              <button
                type="submit"
                disabled={rating < 1 || createMutation.isPending}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {createMutation.isPending ? "Enviando..." : "Enviar reseña"}
              </button>
              {createMutation.isError && (
                <p className="text-sm text-destructive">
                  Error al enviar. Intenta de nuevo.
                </p>
              )}
            </form>

            <ReviewList reviews={data?.reviews ?? []} />
          </>
        )}
      </div>
    </div>
  )
}

function RatingSummary({
  data,
}: {
  data: ProfessorRatingResponse | undefined
}) {
  if (!data || data.total_reviews === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Aun no hay reseñas. Se el primero en calificar.
      </p>
    )
  }

  return (
    <div className="flex items-center gap-3">
      <StarRating rating={data.average_rating} size={20} />
      <span className="text-sm text-muted-foreground">
        {data.average_rating} - {clasificarPromedio(data.average_rating)} ({data.total_reviews} evaluacion{data.total_reviews !== 1 ? "es" : ""})
      </span>
    </div>
  )
}

function ReviewList({ reviews }: { reviews: ProfessorRatingResponse["reviews"] }) {
  if (reviews.length === 0) return null

  return (
    <div className="mt-4 border-t pt-4">
      <p className="mb-2 text-sm font-medium">Reseñas</p>
      <ul className="space-y-3">
        {reviews.map((r) => (
          <li key={r.id} className="rounded border bg-muted/30 p-3 text-sm">
            <div className="flex items-center gap-2">
              <StarRating
                rating={r.promedio ?? r.rating ?? 0}
                size={14}
              />
              <span className="text-muted-foreground">
                {new Date(r.created_at).toLocaleDateString()}
              </span>
            </div>
            {(r.comentario_general || r.comment) && (
              <p className="mt-1">{(r.comentario_general || r.comment) ?? ""}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
