import { useState } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { listDataPdfs, extractFromData } from "@/api/pdf"
import { PdfViewer } from "./PdfViewer"
import { OfertaTable } from "./OfertaTable"
import type { OfertaExtraida } from "@/types/api"

export function DataPdfSelector() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [oferta, setOferta] = useState<OfertaExtraida | null>(null)

  const { data: listData, isLoading: loadingList } = useQuery({
    queryKey: ["pdf-list"],
    queryFn: listDataPdfs,
  })

  const mutation = useMutation({
    mutationFn: extractFromData,
    onSuccess: setOferta,
  })

  const handleSelect = (filename: string) => {
    setSelectedFile(filename)
    setOferta(null)
    mutation.mutate(filename)
  }

  const base = import.meta.env.VITE_API_URL ?? ""
  const pdfSrc = selectedFile
    ? `${base}/api/pdf/file?filename=${encodeURIComponent(selectedFile)}`
    : null

  return (
    <div className="space-y-4">
      <div>
        <h3 className="mb-2 text-sm font-semibold">PDFs en data/</h3>
        {loadingList ? (
          <p className="text-sm text-muted-foreground">Cargando lista...</p>
        ) : listData?.files.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No hay PDFs en el directorio data/. Coloca archivos en ./data/ y
            monta el volumen en Docker.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {listData?.files.map((name) => (
              <button
                key={name}
                onClick={() => handleSelect(name)}
                disabled={mutation.isPending}
                className={`rounded-lg border px-3 py-1.5 text-sm hover:bg-muted ${
                  selectedFile === name ? "border-primary bg-primary/10" : ""
                }`}
              >
                {name}
              </button>
            ))}
          </div>
        )}
      </div>

      {mutation.isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          {mutation.error instanceof Error
            ? mutation.error.message
            : "Error al extraer"}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm font-semibold">Vista previa del PDF</h3>
          <PdfViewer
            src={pdfSrc}
            filename={selectedFile ?? undefined}
          />
        </div>
        <div>
          <h3 className="mb-2 text-sm font-semibold">Materias extraidas</h3>
          <OfertaTable
            materias={oferta?.materias ?? mutation.data?.materias ?? []}
            filas={oferta?.filas ?? mutation.data?.filas}
          />
        </div>
      </div>
    </div>
  )
}
