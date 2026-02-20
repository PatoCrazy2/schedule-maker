import { useOfertaStore } from "@/store/ofertaStore"
import { EvaluarMaestrosSection } from "@/components/EvaluarMaestrosSection"

export function ResenarPage() {
  const { oferta } = useOfertaStore()

  if (!oferta?.materias?.length) {
    return (
      <div className="p-6">
        <h2 className="mb-4 text-xl font-semibold">Resenar</h2>
        <p className="rounded-lg border bg-muted/30 p-6 text-center text-muted-foreground">
          Sube un PDF en la seccion Subir PDF para cargar profesores y poder
          evaluarlos. Una reseña por profesor y materia.
        </p>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h2 className="mb-4 text-xl font-semibold">Resenar</h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Evalua a los profesores del documento cargado. Una reseña por profesor
        y materia.
      </p>
      <EvaluarMaestrosSection materias={oferta.materias} />
    </div>
  )
}
