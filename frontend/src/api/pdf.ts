import { api } from "./client"
import type { OfertaExtraida, PdfListResponse, SourceFileSearchResponse } from "@/types/api"

export async function listDataPdfs(): Promise<PdfListResponse> {
  const { data } = await api.get<PdfListResponse>("/api/pdf/list")
  return data
}

export async function extractFromData(filename: string): Promise<OfertaExtraida> {
  const { data } = await api.post<OfertaExtraida>(
    "/api/pdf/extract-from-data",
    null,
    { params: { filename } }
  )
  return data
}

export async function uploadPdf(
  file: File,
  carrera?: string
): Promise<OfertaExtraida> {
  const formData = new FormData()
  formData.append("file", file)
  if (carrera?.trim()) formData.append("carrera", carrera.trim())
  const { data } = await api.post<OfertaExtraida>("/api/pdf/upload", formData, {
    timeout: 120_000,
    transformRequest: [
      (data: unknown, headers?: Record<string, string>) => {
        if (data instanceof FormData && headers) delete headers["Content-Type"]
        return data
      },
    ],
  })
  return data
}

export async function searchSourceFiles(query: string): Promise<SourceFileSearchResponse[]> {
  const { data } = await api.get<SourceFileSearchResponse[]>("/api/v1/files/search", { params: { q: query } })
  return data
}

export async function getOfertaByHash(fileHash: string): Promise<OfertaExtraida> {
  const { data } = await api.get<OfertaExtraida>(`/api/v1/files/${fileHash}/oferta`)
  return data
}

export interface KardexExtraido {
  materias_aprobadas: string[]
}

export interface ExtractTextResponse {
  texto: string
}

export async function extractTextFromPdf(file: File): Promise<ExtractTextResponse> {
  const formData = new FormData()
  formData.append("file", file)
  const { data } = await api.post<ExtractTextResponse>("/api/pdf/extract-text", formData, {
    timeout: 90_000,
    transformRequest: [
      (payload: unknown, headers?: Record<string, string>) => {
        if (payload instanceof FormData && headers) delete headers["Content-Type"]
        return payload
      },
    ],
  })
  return data
}

export async function uploadHorarioAlumno(file: File): Promise<OfertaExtraida> {
  const formData = new FormData()
  formData.append("file", file)
  const { data } = await api.post<OfertaExtraida>("/api/pdf/upload-horario-alumno", formData, {
    timeout: 90_000,
    transformRequest: [
      (payload: unknown, headers?: Record<string, string>) => {
        if (payload instanceof FormData && headers) delete headers["Content-Type"]
        return payload
      },
    ],
  })
  return data
}

export async function uploadKardex(file: File): Promise<KardexExtraido> {
  const formData = new FormData()
  formData.append("file", file)
  const { data } = await api.post<KardexExtraido>("/api/pdf/upload-kardex", formData, {
    timeout: 60_000,
    transformRequest: [
      (payload: unknown, headers?: Record<string, string>) => {
        if (payload instanceof FormData && headers) delete headers["Content-Type"]
        return payload
      },
    ],
  })
  return data
}
