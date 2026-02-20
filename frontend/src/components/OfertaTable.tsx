import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import type { FilaOferta, MateriaExtraida } from "@/types/api"
import { getProfessorRatingsBatch } from "@/api/professors"
import { diasToNombres } from "@/lib/dias"
import { StarRating } from "./StarRating"
import { ProfessorReviewModal } from "./ProfessorReviewModal"
import { cn } from "@/lib/utils"

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
  if (m.horarios?.length) {
    return m.horarios
      .map((h) =>
        formatHorarioSlot(h.dia, h.hora_inicio, h.hora_fin, h.aula)
      )
      .join("; ")
  }
  if (filas?.length && m.nrc) {
    const matching = filas.filter((f) => f.nrc === m.nrc)
    return matching
      .map((f) =>
        formatHorarioSlot(f.dias, f.hora_inicio, f.hora_fin, f.salon)
      )
      .join("; ")
  }
  return ""
}

export function OfertaTable({ materias, filas, className }: OfertaTableProps) {
  const [modalProfessor, setModalProfessor] = useState<string | null>(null)

  const professorNames = [
    ...new Set(materias.map((m) => m.profesor).filter(Boolean)),
  ] as string[]

  const { data: ratings } = useQuery({
    queryKey: ["professor-ratings", ...professorNames.sort()],
    queryFn: () => getProfessorRatingsBatch(professorNames),
    enabled: professorNames.length > 0,
  })

  if (materias.length === 0) {
    return (
      <p className="py-8 text-center text-muted-foreground">
        No hay materias extraidas
      </p>
    )
  }

  return (
    <div className={cn("overflow-x-auto rounded-lg border", className)}>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="px-3 py-2 font-medium">Clave</th>
            <th className="px-3 py-2 font-medium">Materia</th>
            <th className="px-3 py-2 font-medium">NRC</th>
            <th className="px-3 py-2 font-medium">Grupo</th>
            <th className="px-3 py-2 font-medium">Profesor</th>
            <th className="px-3 py-2 font-medium">Horarios</th>
          </tr>
        </thead>
        <tbody>
          {materias.map((m, i) => (
            <tr key={i} className="border-b last:border-0 hover:bg-muted/30">
              <td className="px-3 py-2">{m.clave ?? "-"}</td>
              <td className="px-3 py-2">{m.nombre}</td>
              <td className="px-3 py-2">{m.nrc ?? "-"}</td>
              <td className="px-3 py-2">{m.grupo ?? "-"}</td>
              <td className="px-3 py-2">
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
              <td className="max-w-sm px-3 py-2 text-muted-foreground">
                {getHorariosParaMateria(m, filas) || "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {modalProfessor && (
        <ProfessorReviewModal
          professorName={modalProfessor}
          onClose={() => setModalProfessor(null)}
        />
      )}
    </div>
  )
}
