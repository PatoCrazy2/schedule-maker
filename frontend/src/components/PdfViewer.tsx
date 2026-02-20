interface PdfViewerProps {
  src: string | null
  filename?: string
}

export function PdfViewer({ src, filename }: PdfViewerProps) {
  if (!src) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-muted-foreground/30 bg-muted/30 text-muted-foreground">
        <p>Selecciona o sube un PDF para visualizarlo</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {filename && (
        <p className="text-sm text-muted-foreground">{filename}</p>
      )}
      <iframe
        src={src}
        title={filename ?? "PDF"}
        className="h-[500px] w-full rounded-lg border bg-white"
      />
    </div>
  )
}
