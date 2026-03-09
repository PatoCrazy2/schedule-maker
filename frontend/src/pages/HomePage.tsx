import { useState, useCallback, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Upload, Search, FileText, ArrowRight } from "lucide-react"
import { uploadPdf, searchSourceFiles, getOfertaByHash } from "@/api/pdf"
import { useOfertaStore } from "@/store/ofertaStore"
import { OfertaTable } from "@/components/OfertaTable"
import { PdfViewer } from "@/components/PdfViewer"

// Hook simple para debounce
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])
  return debouncedValue
}

export function HomePage() {
  const navigate = useNavigate()
  const { oferta, setOferta, clearOferta } = useOfertaStore()
  const [file, setFile] = useState<File | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [carrera, setCarrera] = useState("")

  const [searchQuery, setSearchQuery] = useState("")
  const debouncedSearchQuery = useDebounce(searchQuery, 300)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  const revokePdfUrl = useCallback(() => {
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl)
      setPdfUrl(null)
    }
  }, [pdfUrl])

  // Mutacion para subir nuevo PDF
  const uploadMutation = useMutation({
    mutationFn: ({ file, carrera }: { file: File; carrera?: string }) =>
      uploadPdf(file, carrera),
    onSuccess: (data) => setOferta(data),
    onError: () => revokePdfUrl(),
  })

  // Mutacion para cargar una oferta existente sin PDF
  const fetchOfertaMutation = useMutation({
    mutationFn: (fileHash: string) => getOfertaByHash(fileHash),
    onSuccess: (data) => setOferta(data),
  })

  // Query para buscar archivos existentes
  const { data: searchResults = [] } = useQuery({
    queryKey: ["searchFiles", debouncedSearchQuery],
    queryFn: () => searchSourceFiles(debouncedSearchQuery),
    enabled: debouncedSearchQuery.length > 0 && isDropdownOpen,
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f?.name.toLowerCase().endsWith(".pdf")) return
    revokePdfUrl()
    setFile(f)
    setPdfUrl(URL.createObjectURL(f))
    setOferta(null)
    uploadMutation.reset()
    fetchOfertaMutation.reset()
  }

  const handleUpload = () => {
    if (!file) return
    uploadMutation.mutate({ file, carrera: carrera || undefined })
  }

  const handleSelectExistingFile = (fileHash: string, fileLabel: string) => {
    revokePdfUrl()
    setFile(null)
    setPdfUrl(null)
    clearOferta()
    setIsDropdownOpen(false)
    setSearchQuery(fileLabel)
    uploadMutation.reset()
    fetchOfertaMutation.mutate(fileHash)
  }

  const handleClear = () => {
    revokePdfUrl()
    setFile(null)
    clearOferta()
    setCarrera("")
    setSearchQuery("")
    uploadMutation.reset()
    fetchOfertaMutation.reset()
  }

  const isLoading = uploadMutation.isPending || fetchOfertaMutation.isPending
  const hasError = uploadMutation.isError || fetchOfertaMutation.isError

  return (
    <div className="space-y-6 p-6 pb-24">
      <h2 className="text-xl font-semibold">Subir o Cargar PDF</h2>

      <div className="flex flex-col gap-4 relative z-10">

        {/* Buscador de archivos existentes */}
        <div className="flex flex-col gap-2 max-w-md relative">
          <label className="text-sm font-medium">Buscar archivo existente en el servidor</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar por carrera, archivo o campus..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setIsDropdownOpen(true)
              }}
              onFocus={() => {
                if (searchQuery.length > 0) setIsDropdownOpen(true)
              }}
              onBlur={() => setTimeout(() => setIsDropdownOpen(false), 200)}
              className="w-full rounded-lg border px-9 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {isDropdownOpen && searchResults.length > 0 && (
              <div className="absolute top-full mt-1 w-full bg-background border rounded-lg shadow-lg overflow-hidden z-50 max-h-60 overflow-y-auto">
                {searchResults.map((res) => {
                  const label = res.carrera || res.filename
                  return (
                    <button
                      key={res.file_hash}
                      onClick={() => handleSelectExistingFile(res.file_hash, label)}
                      className="w-full text-left px-4 py-2 text-sm hover:bg-muted focus:bg-muted flex flex-col items-start gap-1"
                    >
                      <span className="font-medium text-foreground">{label}</span>
                      <span className="text-xs text-muted-foreground flex gap-2">
                        {res.facultad && <span>{res.facultad}</span>}
                        {res.campus && <span>• {res.campus}</span>}
                        {res.periodo && <span>• {res.periodo}</span>}
                      </span>
                    </button>
                  )
                })}
              </div>
            )}
            {isDropdownOpen && debouncedSearchQuery.length > 0 && searchResults.length === 0 && (
              <div className="absolute top-full mt-1 w-full bg-background border rounded-lg shadow-lg p-3 text-sm text-muted-foreground z-50">
                No se encontraron archivos.
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 py-2">
          <div className="h-px bg-border flex-1 max-w-[50px]"></div>
          <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">o subir archivo</span>
          <div className="h-px bg-border flex-1 max-w-[500px]"></div>
        </div>

        {/* Subida de un nuevo archivo */}
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-primary bg-primary/10 px-4 py-2 text-sm font-medium hover:bg-primary/20">
            <Upload size={18} />
            Seleccionar PDF
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
          <button
            onClick={handleUpload}
            disabled={!file || isLoading}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isLoading && !fetchOfertaMutation.isPending ? "Procesando..." : "Subir y extraer"}
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
      </div>

      {hasError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          Error al procesar o cargar la oferta. Por favor, intente de nuevo.
        </div>
      )}

      {fetchOfertaMutation.isPending && (
        <div className="p-8 text-center text-sm text-muted-foreground animate-pulse border rounded-lg bg-muted/20">
          Cargando datos de la base de datos...
        </div>
      )}

      <div className={`grid gap-6 ${pdfUrl ? "lg:grid-cols-2" : "grid-cols-1"}`}>
        {pdfUrl && (
          <div>
            <h3 className="mb-2 text-sm font-semibold flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Vista previa del PDF
            </h3>
            <PdfViewer src={pdfUrl} filename={file?.name} />
          </div>
        )}
        <div>
          <h3 className="mb-2 text-sm font-semibold">Materias extraidas</h3>
          <OfertaTable
            materias={oferta?.materias ?? []}
            filas={oferta?.filas}
          />
        </div>
      </div>

      {oferta && (
        <div className="fixed bottom-0 left-0 right-0 z-50 flex justify-center border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <button
            onClick={() => navigate("/crear-horario")}
            className="flex items-center gap-2 rounded-lg bg-primary px-8 py-3 text-base font-semibold text-primary-foreground shadow-lg transition-transform hover:-translate-y-0.5 hover:bg-primary/90 active:translate-y-0"
          >
            Siguiente: Crear Horario
            <ArrowRight size={20} />
          </button>
        </div>
      )}
    </div>
  )
}
