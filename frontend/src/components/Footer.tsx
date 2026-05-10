import { Github } from "lucide-react"

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="w-full border-t border-border bg-background py-8 mt-auto">
      <div className="mx-auto max-w-6xl px-4">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">

          {/* Lado Izquierdo: Identidad y Copyright */}
          <div className="flex flex-col gap-1 text-center md:text-left">
            <span className="text-sm font-semibold text-foreground">
              Schedule Maker BUAP
            </span>
            <p className="text-xs text-muted-foreground">
              © {currentYear} — Herramienta de planificación académica.
            </p>
          </div>

          {/* Centro: Desarrolladores */}
          <div className="flex items-center gap-6">
            <div className="flex flex-col items-center gap-1 md:items-start">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                Desarrollo
              </span>
              <div className="flex items-center gap-4">
                <a
                  href="https://github.com/PatoCrazy2"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 text-xs text-foreground hover:text-primary transition-colors"
                >
                  <Github size={12} />
                  <span>PatoCrazy2</span>
                </a>
                <a
                  href="https://github.com/joseraulsoriano" // Placeholder para el colaborador
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 text-xs text-foreground hover:text-primary transition-colors"
                >
                  <Github size={12} />
                  <span>joseraulsoriano</span>
                </a>
              </div>
            </div>
          </div>

          {/* Lado Derecho: Repo y Licencia */}
          <div className="flex flex-col items-center gap-1 md:items-end">
            <a
              href="https://github.com/PatoCrazy2/schedule-maker"
              target="_blank"
              rel="noreferrer"
              className="text-xs font-medium text-foreground hover:underline"
            >
              Repositorio del Proyecto
            </a>
            <span className="text-[10px] text-muted-foreground uppercase tracking-tight">
              MIT License · Open Source
            </span>
          </div>

        </div>
      </div>
    </footer>
  )
}
