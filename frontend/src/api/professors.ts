import { api } from "./client"
import type {
  ProfessorListItem,
  ProfessorRatingResponse,
  ProfessorReviewCreate,
} from "@/types/api"

export async function createProfessorReview(
  data: ProfessorReviewCreate
): Promise<void> {
  await api.post("/api/professors/reviews", data)
}

export async function getProfessorReviews(
  professorName: string
): Promise<ProfessorRatingResponse> {
  const { data } = await api.get<ProfessorRatingResponse>(
    `/api/professors/${encodeURIComponent(professorName)}/reviews`
  )
  return data
}

export interface ProfessorRatingBatch {
  [professorName: string]: { average_rating: number; total_reviews: number }
}

export async function listProfessors(): Promise<ProfessorListItem[]> {
  const { data } = await api.get<ProfessorListItem[]>("/api/professors/list")
  return data
}

export async function getProfessorRatingsBatch(
  names: string[]
): Promise<ProfessorRatingBatch> {
  const unique = [...new Set(names)].filter(Boolean)
  if (unique.length === 0) return {}
  const params = new URLSearchParams()
  unique.forEach((n) => params.append("names", n))
  const { data } = await api.get<ProfessorRatingBatch>(
    `/api/professors/ratings/batch?${params}`
  )
  return data
}
