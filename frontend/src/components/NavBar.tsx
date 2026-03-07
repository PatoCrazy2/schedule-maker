import { NavLink } from "react-router-dom"
import { Home, Calendar } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", icon: Home, label: "Inicio" },
  { to: "/crear-horario", icon: Calendar, label: "Crear horario" },
]

export function NavBar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex max-w-6xl items-center gap-1 px-4 py-2">
        <NavLink
          to="/"
          className="mr-4 text-lg font-semibold text-primary"
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
