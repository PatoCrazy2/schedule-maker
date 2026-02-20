import { useState, useCallback } from "react"
import { useMutation } from "@tanstack/react-query"
import { Upload } from "lucide-react"
import { uploadPdf } from "@/api/pdf"
import { EvaluarMaestrosSection } from "./EvaluarMaestrosSection"
import { OfertaTable } from "./OfertaTable"
import { PdfViewer } from "./PdfViewer"
import type { OfertaExtraida } from "@/types/api"

export function PdfUploader() {
  const [file, setFile] = useState<File | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [oferta, setOferta] = useState<OfertaExtraida | null>(null)
  const [carrera, setCarrera] = useState("")

  const revokePdfUrl = useCallback(() => {
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl)
      setPdfUrl(null)
    }
  }, [pdfUrl])

  const mutation = useMutation({
    mutationFn: ({ file, carrera }: { file: File; carrera?: string }) =>
      uploadPdf(file, carrera),
    onSuccess: (data) => setOferta(data),
    onError: () => revokePdfUrl(),
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f?.name.toLowerCase().endsWith(".pdf")) return
    revokePdfUrl()
    setFile(f)
    setPdfUrl(URL.createObjectURL(f))
    setOferta(null)
    mutation.reset()
  }

  const handleUpload = () => {
    if (!file) return
    mutation.mutate({ file, carrera: carrera || undefined })
  }

  const handleClear = () => {
    revokePdfUrl()
    setFile(null)
    setOferta(null)
    setCarrera("")
    mutation.reset()
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="Carrera / profesión (opcional)"
          value={carrera}
          onChange={(e) => setCarrera(e.target.value)}
          className="rounded-lg border px-3 py-2 text-sm"
        />
        <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-primary bg-primary/10 px-4 py-2 text-sm font-medium hover:bg-primary/20">
          <Upload size={18} />
          <span>Seleccionar PDF</span>
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>
        <button
          onClick={handleUpload}
          disabled={!file || mutation.isPending}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {mutation.isPending ? "Procesando..." : "Subir y extraer"}
        </button>
        {(file || oferta) && (
          <button
            onClick={handleClear}
            className="rounded-lg border px-4 py-2 text-sm hover:bg-muted"
          >
            Limpiar
          </button>
        )}
      </div>

      {mutation.isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          {mutation.error instanceof Error
            ? mutation.error.message
            : "Error al procesar el PDF"}
        </div>
      )}

      <div className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-semibold">Vista previa del PDF</h3>
            <PdfViewer src={pdfUrl} filename={file?.name} />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold">Materias extraidas</h3>
            <OfertaTable
              materias={oferta?.materias ?? []}
              filas={oferta?.filas}
            />
          </div>
        </div>

        {oferta && oferta.materias.length > 0 && (
          <EvaluarMaestrosSection materias={oferta.materias} />
        )}
      </div>
    </div>
  )
}
