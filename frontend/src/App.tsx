import { Routes, Route } from "react-router-dom"
import { NavBar } from "@/components/NavBar"
import { HomePage } from "@/pages/HomePage"
import { CrearHorarioPage } from "@/pages/CrearHorarioPage"
import { PresentarHorarioPage } from "@/pages/PresentarHorarioPage"

export default function App() {
  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <NavBar />
      <main className="w-full">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/crear-horario" element={<CrearHorarioPage />} />
          <Route path="/presentar-horario" element={<PresentarHorarioPage />} />
        </Routes>
      </main>
    </div>
  )
}
