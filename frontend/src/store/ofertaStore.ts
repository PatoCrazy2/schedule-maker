import { create } from "zustand"
import type { OfertaExtraida } from "@/types/api"

interface OfertaState {
  oferta: OfertaExtraida | null
  setOferta: (o: OfertaExtraida | null) => void
  clearOferta: () => void
}

export const useOfertaStore = create<OfertaState>((set) => ({
  oferta: null,
  setOferta: (o) => set({ oferta: o }),
  clearOferta: () => set({ oferta: null }),
}))
