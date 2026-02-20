/**
 * Instrumento formal de evaluacion docente.
 * Escala: 1=Muy deficiente, 2=Deficiente, 3=Aceptable, 4=Bueno, 5=Excelente
 */

export const ESCALA_LABELS: Record<number, string> = {
  1: "Muy deficiente",
  2: "Deficiente",
  3: "Aceptable",
  4: "Bueno",
  5: "Excelente",
}

export const METRICAS = [
  {
    key: "dominio_contenido",
    label: "Dominio del contenido",
    pregunta:
      "Que tan solido es el conocimiento del profesor sobre la materia?",
    justificacionKey: "justificacion_dominio",
  },
  {
    key: "claridad",
    label: "Claridad en la explicacion",
    pregunta: "Que tan clara y estructurada es su forma de ensenar?",
    justificacionKey: "justificacion_claridad",
  },
  {
    key: "metodologia",
    label: "Metodologia de ensenanza",
    pregunta:
      "Utiliza ejemplos, ejercicios o recursos que faciliten el aprendizaje?",
    justificacionKey: "justificacion_metodologia",
  },
  {
    key: "justicia_evaluacion",
    label: "Justicia en evaluacion",
    pregunta:
      "Los examenes y trabajos reflejan lo visto en clase y son justos?",
    justificacionKey: "justificacion_justicia",
  },
  {
    key: "exigencia",
    label: "Nivel de exigencia academica",
    pregunta: "El nivel de dificultad contribuye al aprendizaje real?",
    justificacionKey: "justificacion_exigencia",
  },
  {
    key: "apoyo",
    label: "Retroalimentacion y apoyo",
    pregunta:
      "Brinda apoyo, responde dudas y ofrece retroalimentacion util?",
    justificacionKey: "justificacion_apoyo",
  },
  {
    key: "organizacion",
    label: "Organizacion y gestion del curso",
    pregunta: "La clase esta bien estructurada y organizada?",
    justificacionKey: "justificacion_organizacion",
  },
  {
    key: "impacto",
    label: "Impacto en tu aprendizaje",
    pregunta:
      "Consideras que aprendiste habilidades o conocimientos valiosos?",
    justificacionKey: "justificacion_impacto",
  },
] as const

export function clasificarPromedio(prom: number): string {
  if (prom >= 4.5) return "Excelente"
  if (prom >= 4.0) return "Muy bueno"
  if (prom >= 3.0) return "Aceptable"
  if (prom >= 2.0) return "Bajo"
  return "Deficiente"
}
