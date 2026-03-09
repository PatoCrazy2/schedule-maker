import { useState, useEffect } from "react"
import { NavLink } from "react-router-dom"
import { Home, Calendar, Presentation } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", icon: Home, label: "Inicio" },
  { to: "/crear-horario", icon: Calendar, label: "Crear horario" },
  { to: "/presentar-horario", icon: Presentation, label: "Presentar horario" },
]

export function NavBar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener("scroll", onScroll)
    onScroll()
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <nav
      className={cn(
        "sticky top-0 z-50 w-full border-b backdrop-blur transition-colors",
        scrolled ? "bg-transparent border-transparent" : "bg-background/95 border-border supports-[backdrop-filter]:bg-background/60"
      )}
    >
      <div className="mx-auto flex max-w-6xl items-center gap-1 px-4 py-2">
        <NavLink
          to="/"
          className="mr-4 text-lg font-semibold text-primary"
          onClick={(e) => {
            // Si ya estamos en la página de inicio, evitamos la recarga y hacemos scroll
            if (window.location.pathname === "/") {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: "smooth" });
            }
          }}
        >
          Schedule Maker
        </NavLink>
        <div className="flex flex-1 flex-wrap gap-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
