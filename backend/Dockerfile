# backend/Dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema para Camelot y OpenCV
RUN apt-get update && apt-get install -y \
    ghostscript \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY ./app /code/app

# Comando de arranque
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]