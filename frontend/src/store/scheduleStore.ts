import { create } from "zustand"
import type { MateriaExtraida } from "@/types/api"

export interface ScheduleOption {
  materias: MateriaExtraida[]
  score?: number
}

interface ScheduleState {
  selectedMaterias: MateriaExtraida[]
  selectedSchedule: ScheduleOption | null
  setSelectedMaterias: (m: MateriaExtraida[]) => void
  setSelectedSchedule: (s: ScheduleOption | null) => void
  toggleMateria: (m: MateriaExtraida) => void
  clearSchedule: () => void
}

export const useScheduleStore = create<ScheduleState>((set) => ({
  selectedMaterias: [],
  selectedSchedule: null,
  setSelectedMaterias: (m) => set({ selectedMaterias: m }),
  setSelectedSchedule: (s) => set({ selectedSchedule: s }),
  toggleMateria: (materia) =>
    set((state) => {
      const key = (m: MateriaExtraida) => `${m.nrc ?? ""}-${m.grupo ?? ""}`
      const exists = state.selectedMaterias.some(
        (x) => key(x) === key(materia)
      )
      if (exists) {
        return {
          selectedMaterias: state.selectedMaterias.filter(
            (x) => key(x) !== key(materia)
          ),
        }
      }
      return {
        selectedMaterias: [...state.selectedMaterias, materia],
      }
    }),
  clearSchedule: () =>
    set({ selectedMaterias: [], selectedSchedule: null }),
}))
