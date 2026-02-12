# Schedule Maker - Backend

API FastAPI para extraer oferta desde PDF, generar horarios y exportar (PDF, ICS, Google Calendar).

## Levantar con Docker

Solo backend + Postgres. Los PDF de prueba van en `data/` (raíz del repo), montada en el contenedor.

Hay un **docker-compose.yml en la raíz del repo** (schedule-maker). Usa ese para no depender del directorio:

Desde la **raíz del repositorio** (carpeta schedule-maker):

```bash
cd "/Users/chasse/PROYECTOS PERSONALES/LIFE OF CHASSE/PROGRAMMING/web/PDF/schedule-maker"
docker compose up -d
```

Para **reiniciar** el backend:

```bash
docker compose restart backend
```

Para **reconstruir** la imagen (tras cambiar Dockerfile o requirements.txt):

```bash
docker compose build --no-cache backend
docker compose up -d
```

(Sigue siendo necesario estar en la raíz del repo, donde está el docker-compose.yml.)

Alternativa: si prefieres usar el compose que está dentro de `backend/`, entra primero en esa carpeta y luego ejecuta `docker compose up -d`.

Quedan el API en **http://localhost:8000** y la documentación en **http://localhost:8000/docs**.

Para construir solo la imagen del backend (sin compose):

```bash
cd backend
docker build -t schedule-backend .
docker run --rm -p 8000:8000 -v "$(pwd)/../data:/code/data" -e SCHEDULE_DATA_DIR=/code/data schedule-backend
```

## Uso de la carpeta data/

Los PDF que coloques en `data/` (por ejemplo `Ajustes Banner 2026.pdf`) se montan en el contenedor en `/code/data`. Puedes:

- **Listar PDF disponibles**: `GET /api/pdf/list`
- **Extraer desde un archivo en data**: `POST /api/pdf/extract-from-data?filename=Ajustes%20Banner%202026.pdf`
- **Subir otro PDF**: `POST /api/pdf/upload` (multipart)

## Estructura (parser tipo contable)

- `app/services/lector_pdf.py`: lee PDF y devuelve texto + tablas (pdfplumber).
- `app/services/parsers/base_parser.py`: interfaz de parsers de oferta.
- `app/services/parsers/banner_parser.py`: parser para ofertas tipo Banner/BUAP.
- `app/services/parser_factory.py`: elige el parser según contenido/archivo.
- `app/services/parser_oferta.py`: orquesta lector + factory y devuelve `OfertaExtraida`.
