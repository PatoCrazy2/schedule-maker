import { create } from "zustand"

interface KardexState {
  materiasAprobadas: string[]
  kardexFileName: string | null
  setMateriasAprobadas: (m: string[]) => void
  setKardexFileName: (name: string | null) => void
  clearKardex: () => void
}

export const useKardexStore = create<KardexState>((set) => ({
  materiasAprobadas: [],
  kardexFileName: null,
  setMateriasAprobadas: (m) => set({ materiasAprobadas: m }),
  setKardexFileName: (name) => set({ kardexFileName: name }),
  clearKardex: () =>
    set({ materiasAprobadas: [], kardexFileName: null }),
}))
