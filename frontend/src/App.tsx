import { Routes, Route } from "react-router-dom"
import { NavBar } from "@/components/NavBar"
import { HomePage } from "@/pages/HomePage"
import { SubirPdfPage } from "@/pages/SubirPdfPage"
import { VerProfesoresPage } from "@/pages/VerProfesoresPage"
import { ResenarPage } from "@/pages/ResenarPage"
import { CrearHorarioPage } from "@/pages/CrearHorarioPage"

export default function App() {
  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      <main className="mx-auto max-w-6xl">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/subir-pdf" element={<SubirPdfPage />} />
          <Route path="/ver-profesores" element={<VerProfesoresPage />} />
          <Route path="/resenar" element={<ResenarPage />} />
          <Route path="/crear-horario" element={<CrearHorarioPage />} />
        </Routes>
      </main>
    </div>
  )
}
