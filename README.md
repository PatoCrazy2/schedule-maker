# 📅 Schedule Maker - BUAP

[![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20PostgreSQL-blue)](https://github.com/PatoCrazy2/schedule-maker)
[![Status](https://img.shields.io/badge/Status-Beta-orange)](#)

**Schedule Maker** es una solución integral diseñada para la comunidad de la **Benemérita Universidad Autónoma de Puebla (BUAP), Facultad de Ciencias de la Computación (FCC)**. Su objetivo es simplificar el caótico proceso de inscripción, permitiendo a los estudiantes generar horarios óptimos, libres de traslapes, a partir de archivos PDF de oferta académica.

---

## 🚀 ¿Qué hace la App?

La aplicación automatiza la extracción de datos de documentos oficiales y proporciona herramientas inteligentes de planificación:

1.  **Extracción Inteligente (PDF Parsing)**: Procesa PDFs de oferta académica (Banner BUAP), kardex y horarios de alumnos. Utiliza técnicas de extracción directa de texto y **OCR (Tesseract)** para documentos escaneados.
2.  **Generación de Horarios**: Algoritmo que calcula combinaciones de materias seleccionadas asegurando que no existan conflictos de horario.
3.  **Gestión de Académica**:
    *   Carga de Kardex para filtrar materias ya aprobadas.
    *   Carga de Mapas Curriculares para seguir el progreso del plan de estudios.
4.  **Exportación Multiformato**:
    *   Generación de horarios en PDF.
    *   Sincronización con **Google Calendar**.
    *   Exportación de archivos `.ics` para **Apple Calendar**.

---

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Framework moderno y de alto rendimiento para la API.
- **SQLModel (Pydantic + SQLAlchemy)**: Para la interacción con la base de datos PostgreSQL.
- **PostgreSQL**: Almacenamiento persistente de oferta, cursos y archivos.
- **Redis**: Capa de caché para acelerar la extracción de documentos repetidos (hashing).
- **PDFPlumber & Tesseract**: Motores de extracción de datos y OCR.

### Frontend
- **React + Vite**: Interfaz de usuario rápida y reactiva.
- **Tailwind CSS**: Estilizado moderno y responsivo.
- **TypeScript**: Tipado estático para mayor mantenibilidad.

### Infraestructura
- **Docker & Docker Compose**: Contenerización para un entorno de desarrollo consistente.

---

## 💻 Ejecución Local

Para levantar el proyecto en tu máquina local, asegúrate de tener instalado [Docker](https://www.docker.com/).

### 1. Clonar el repositorio
```bash
git clone https://github.com/PatoCrazy2/schedule-maker.git
cd schedule-maker
```

### 2. Configurar variables de entorno
Crea un archivo `.env` en la raíz (puedes basarte en los ejemplos del backend):
```env
DATABASE_URL=postgresql://user:password@db:5432/schedule_db
REDIS_URL=redis://redis:6379/0
```

### 3. Levantar servicios
Ejecuta el siguiente comando para iniciar el Backend y la Base de Datos:
```bash
docker-compose up -d
```
*   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Backend**: [http://localhost:8000](http://localhost:8000)

### 4. Frontend (Desarrollo)
Entra a la carpeta frontend e instala dependencias:
```bash
cd frontend
npm install
npm run dev
```
*   **App**: [http://localhost:5173](http://localhost:5173)

---

## 🌐 Despliegue (Deploy)

El proyecto se encuentra actualmente desplegado utilizando una arquitectura híbrida:
- **Backend**: Desplegado en **Render** (o plataforma similar con contenedores).
- **Frontend**: Servido como aplicación estática.

> [!IMPORTANT]
> **Aviso de Cold Start**: Debido a que estamos utilizando un tier gratuito para el despliegue del backend, es posible que la primera solicitud tarde entre **30 y 60 segundos** en responder mientras el servidor se "despierta" (Cold Start). Una vez activo, el rendimiento será óptimo.

---

## 🏗️ Estructura del Proyecto

```text
.
├── backend/          # API REST (FastAPI)
├── frontend/         # Interfaz de Usuario (React)
├── data/             # Directorio para PDFs de prueba (montado en Docker)
├── docker-compose.yml # Orquestación de servicios locales
└── Intro.md          # Documentación técnica inicial
```

---

## 🤝 Contribuciones

Si eres estudiante de la BUAP y quieres mejorar esta herramienta, ¡las PRs son bienvenidas! 

1. Haz un Fork del proyecto.
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`).
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`).
4. Haz Push a la rama (`git push origin feature/AmazingFeature`).
5. Abre un Pull Request.

---

Desarrollado con ❤️ para la comunidad estudiantil.
