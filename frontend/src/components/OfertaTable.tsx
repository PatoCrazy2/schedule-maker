import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { Search, ChevronLeft, ChevronRight } from "lucide-react"
import type { FilaOferta, MateriaExtraida } from "@/types/api"
import { getProfessorRatingsBatch } from "@/api/professors"
import { diasToNombres } from "@/lib/dias"
import { StarRating } from "./StarRating"
import { ProfessorReviewModal } from "./ProfessorReviewModal"
import { cn } from "@/lib/utils"

const ROWS_PER_PAGE = 10

interface OfertaTableProps {
  materias: MateriaExtraida[]
  filas?: FilaOferta[]
  className?: string
}

function formatHorarioSlot(
  dia: string,
  horaInicio: string,
  horaFin: string,
  aula?: string
): string {
  const diaNombre = diasToNombres(dia)
  const hora = [horaInicio, horaFin].filter(Boolean).join("-")
  const parte = diaNombre ? `${diaNombre} ${hora}` : hora
  return aula ? `${parte} (${aula})` : parte
}

function getHorariosParaMateria(
  m: MateriaExtraida,
  filas: FilaOferta[] | undefined
): string {
  return getHorariosArray(m, filas).join("; ")
}

function getHorariosArray(
  m: MateriaExtraida,
  filas: FilaOferta[] | undefined
): string[] {
  if (m.horarios?.length) {
    return m.horarios.map((h) =>
      formatHorarioSlot(h.dia, h.hora_inicio, h.hora_fin, h.aula)
    )
  }
  if (filas?.length && m.nrc) {
    const matching = filas.filter((f) => f.nrc === m.nrc)
    return matching.map((f) =>
      formatHorarioSlot(f.dias, f.hora_inicio, f.hora_fin, f.salon)
    )
  }
  return []
}

function materiaCoincideBusqueda(m: MateriaExtraida, filas: FilaOferta[] | undefined, q: string): boolean {
  if (!q.trim()) return true
  const term = q.toLowerCase().trim()
  const horarios = getHorariosParaMateria(m, filas).toLowerCase()
  const partes = [
    m.clave ?? "",
    m.nombre ?? "",
    m.nrc ?? "",
    m.grupo ?? "",
    m.profesor ?? "",
    horarios,
  ]
  return partes.some((p) => p.includes(term))
}

export function OfertaTable({ materias, filas, className }: OfertaTableProps) {
  const [modalProfessor, setModalProfessor] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [currentPage, setCurrentPage] = useState(1)

  const materiasFiltradas = useMemo(() => {
    return materias.filter((m) => materiaCoincideBusqueda(m, filas, searchQuery))
  }, [materias, filas, searchQuery])

  const totalPages = Math.max(1, Math.ceil(materiasFiltradas.length / ROWS_PER_PAGE))
  const pageIndex = Math.min(currentPage, totalPages)
  const materiasPaginadas = useMemo(() => {
    const start = (pageIndex - 1) * ROWS_PER_PAGE
    return materiasFiltradas.slice(start, start + ROWS_PER_PAGE)
  }, [materiasFiltradas, pageIndex])

  const professorNames = [
    ...new Set(materias.map((m) => m.profesor).filter(Boolean)),
  ] as string[]

  const { data: ratings } = useQuery({
    queryKey: ["professor-ratings", ...professorNames.sort()],
    queryFn: () => getProfessorRatingsBatch(professorNames),
    enabled: professorNames.length > 0,
  })

  const handleSearchChange = (q: string) => {
    setSearchQuery(q)
    setCurrentPage(1)
  }

  if (materias.length === 0) {
    return (
      <p className="py-8 text-center text-muted-foreground">
        No hay materias extraidas
      </p>
    )
  }

  if (materiasFiltradas.length === 0) {
    return (
      <div className={cn("flex flex-col gap-3", className)}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar por clave, materia, NRC, grupo, profesor, horario..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full rounded-lg border pl-9 pr-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <p className="py-8 text-center text-muted-foreground">
          No hay coincidencias para &quot;{searchQuery}&quot;
        </p>
      </div>
    )
  }

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Buscar por clave, materia, NRC, grupo, profesor, horario..."
          value={searchQuery}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full rounded-lg border pl-9 pr-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="border-r border-border px-3 py-2 font-medium whitespace-nowrap">Clave</th>
              <th className="border-r border-border px-3 py-2 font-medium whitespace-nowrap">Materia</th>
              <th className="border-r border-border px-3 py-2 font-medium whitespace-nowrap">NRC</th>
              <th className="border-r border-border px-3 py-2 font-medium whitespace-nowrap">Grupo</th>
              <th className="border-r border-border px-3 py-2 font-medium whitespace-nowrap">Profesor</th>
              <th className="px-3 py-2 font-medium whitespace-nowrap">Horarios</th>
            </tr>
          </thead>
          <tbody>
            {materiasPaginadas.map((m) => {
              const slots = getHorariosArray(m, filas)
              return (
            <tr key={`${m.nrc}-${m.grupo}`} className="border-b border-border last:border-b-0 hover:bg-muted/30">
              <td className="border-r border-border px-3 py-2 align-top">{m.clave ?? "-"}</td>
              <td className="border-r border-border px-3 py-2 align-top">{m.nombre}</td>
              <td className="border-r border-border px-3 py-2 align-top">{m.nrc ?? "-"}</td>
              <td className="border-r border-border px-3 py-2 align-top">{m.grupo ?? "-"}</td>
              <td className="border-r border-border px-3 py-2 align-top">
                {m.profesor ? (
                  <button
                    type="button"
                    onClick={() => setModalProfessor(m.profesor!)}
                    className="inline-flex items-center gap-2 text-left hover:underline"
                  >
                    <span>{m.profesor}</span>
                    {ratings?.[m.profesor]?.total_reviews ? (
                      <StarRating
                        rating={ratings[m.profesor].average_rating}
                        size={14}
                      />
                    ) : null}
                  </button>
                ) : (
                  "-"
                )}
              </td>
              <td className="px-3 py-2 align-top min-w-[200px]">
                {slots.length > 0 ? (
                  <div className="flex flex-col gap-2">
                    {slots.map((slot, i) => (
                      <div
                        key={i}
                        className="rounded-md border border-border/60 bg-muted/50 px-2.5 py-1.5 text-xs text-muted-foreground"
                      >
                        {slot}
                      </div>
                    ))}
                  </div>
                ) : (
                  "-"
                )}
              </td>
            </tr>
            )
            })}
        </tbody>
      </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between gap-4 text-sm">
          <span className="text-muted-foreground">
            {materiasFiltradas.length} materias
            {searchQuery && ` (filtradas)`}
            {" · "}
            Pag. {pageIndex} de {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={pageIndex <= 1}
              className="rounded border p-1.5 hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Pagina anterior"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={pageIndex >= totalPages}
              className="rounded border p-1.5 hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Pagina siguiente"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {modalProfessor && (
        <ProfessorReviewModal
          professorName={modalProfessor}
          onClose={() => setModalProfessor(null)}
        />
      )}
    </div>
  )
}
