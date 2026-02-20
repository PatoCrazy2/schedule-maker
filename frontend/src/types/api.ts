/** Tipos que coinciden con los schemas del backend (OfertaExtraida, MateriaExtraida, etc.) */

export interface HorarioSlot {
  dia: string
  hora_inicio: string
  hora_fin: string
  aula?: string
}

export interface MateriaExtraida {
  nrc?: string
  nombre: string
  clave?: string
  grupo?: string
  horarios: HorarioSlot[]
  profesor?: string
  creditos?: number
  aula?: string
}

export interface FilaOferta {
  nrc: string
  clave: string
  materia: string
  secc: string
  dias: string
  hora_inicio: string
  hora_fin: string
  profesor: string
  salon: string
}

export interface OfertaExtraida {
  filas: FilaOferta[]
  materias: MateriaExtraida[]
  archivos_procesados: string[]
}

export interface PdfListResponse {
  files: string[]
  data_dir: string
}

export interface ProfessorReviewCreate {
  professor_name: string
  materia_nombre?: string
  dominio_contenido?: number
  claridad?: number
  metodologia?: number
  justicia_evaluacion?: number
  exigencia?: number
  apoyo?: number
  organizacion?: number
  impacto?: number
  justificacion_dominio?: string
  justificacion_claridad?: string
  justificacion_metodologia?: string
  justificacion_justicia?: string
  justificacion_exigencia?: string
  justificacion_apoyo?: string
  justificacion_organizacion?: string
  justificacion_impacto?: string
  comentario_general?: string
  rating?: number
  comment?: string
}

export interface ProfessorReviewRead {
  id: number
  professor_name: string
  materia_nombre: string | null
  dominio_contenido: number | null
  claridad: number | null
  metodologia: number | null
  justicia_evaluacion: number | null
  exigencia: number | null
  apoyo: number | null
  organizacion: number | null
  impacto: number | null
  justificacion_dominio: string | null
  justificacion_claridad: string | null
  justificacion_metodologia: string | null
  justificacion_justicia: string | null
  justificacion_exigencia: string | null
  justificacion_apoyo: string | null
  justificacion_organizacion: string | null
  justificacion_impacto: string | null
  comentario_general: string | null
  promedio: number | null
  rating: number | null
  comment: string | null
  created_at: string
}

export interface ProfessorCourseDetail {
  nrc: string
  clave: string
  nombre: string
  grupo: string
  horarios: HorarioSlot[]
}

export interface ProfessorListItem {
  name: string
  materias: string[]
  courses?: ProfessorCourseDetail[]
  average_rating: number
  total_reviews: number
}

export interface ProfessorRatingResponse {
  professor_name: string
  average_rating: number
  total_reviews: number
  reviews: ProfessorReviewRead[]
}
