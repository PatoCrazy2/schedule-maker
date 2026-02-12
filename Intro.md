# Schedule Maker - Generador de horarios BUAP

## Descripción del proyecto

Aplicación web de uso local orientada a la comunidad de la **Benemérita Universidad Autónoma de Puebla (BUAP)** y entornos similares. Permite subir documentos PDF con ofertas de materias o horarios, extraer la información de forma automática y generar horarios óptimos para inscripción de materias.

## Flujo principal

1. **Carga de PDF**: El usuario sube uno o más PDF (por ejemplo, oferta de materias por facultad o periodo).
2. **Extracción de información**: El sistema procesa los PDF y obtiene datos estructurados: nombre de materia, claves, grupos, horarios (días y horas), profesor, aula, etc.
3. **Construcción del horario**: A partir de las materias seleccionadas o filtros (carrera, nivel, preferencias), se calculan las mejores combinaciones de grupos que no se traslapan.
4. **Exportación**:
   - **PDF**: Generar un horario en PDF (editable o de solo lectura, según se defina).
   - **Google Calendar**: Exportar eventos al calendario de Google.
   - **Apple Calendar**: Exportar en formato compatible (por ejemplo, `.ics`) para importar en Calendario de Apple.

## Alcance técnico

- **Backend**: API REST con FastAPI; endpoints para subida de PDF, extracción, generación de horarios y exportación (PDF, ICS/Google/Apple). La extracción sigue un patrón de **lector + parser** (inspirado en el proyecto contable): `LectorPDF` obtiene texto y tablas; `ParserFactory` elige el parser (p. ej. Banner/BUAP) y se obtiene oferta estructurada.
- **Frontend**: Interfaz para subir archivos, visualizar materias y horarios, elegir opciones y descargar/exportar.
- **Ejecución**: Pensado para despliegue local o en red interna (comunidad BUAP); no es un servicio público en internet.

## Cómo levantar el backend

El backend se levanta con **Docker** (ver `backend/Dockerfile` y `docker-compose.yml`). Los PDF de prueba se colocan en la carpeta **`data/`** en la raíz del repo; ese directorio se monta en el contenedor.

Desde la raíz del repositorio:

```bash
docker-compose up backend
```

API en http://localhost:8000 y documentación en http://localhost:8000/docs. Endpoints útiles: `GET /api/pdf/list` (lista PDF en `data/`), `POST /api/pdf/extract-from-data?filename=...` (extrae desde un PDF en `data/`), `POST /api/pdf/upload` (subir y extraer otro PDF).

## Próximos pasos

- Definir formato exacto de los PDF de entrada (ej. tablas de oferta BUAP) para afinar la extracción.
- Implementar reglas de conflicto (traslapes) y criterios de "mejor opción" (ej. menos huecos, preferencia de horario).
- Integrar generación de PDF y flujos OAuth/export para Google Calendar y archivo ICS para Apple.
