"""
Migracion: agrega columna carrera a source_file.
Ejecutar con: python -m scripts.add_carrera_column
(desde el directorio backend, con PYTHONPATH incluyendo el backend)
"""
import os
import sys

# Asegurar que el backend este en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SCHEDULE_DATABASE_URL", "postgresql://user:password@localhost:5432/schedule_db")

from sqlalchemy import text
from app.core.database import engine

if __name__ == "__main__":
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE source_file ADD COLUMN IF NOT EXISTS carrera VARCHAR(255)"))
    print("Columna carrera agregada (o ya existia).")
