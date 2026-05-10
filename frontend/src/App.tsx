import { Routes, Route } from "react-router-dom"
import { NavBar } from "@/components/NavBar"
import { Footer } from "@/components/Footer"
import { HomePage } from "@/pages/HomePage"
import { CrearHorarioPage } from "@/pages/CrearHorarioPage"
import { PresentarHorarioPage } from "@/pages/PresentarHorarioPage"

export default function App() {
  return (
    <div className="flex min-h-screen flex-col bg-background overflow-x-hidden">
      <NavBar />
      <main className="flex-1 w-full">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/crear-horario" element={<CrearHorarioPage />} />
          <Route path="/presentar-horario" element={<PresentarHorarioPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
