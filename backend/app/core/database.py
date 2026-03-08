import time
import logging
from typing import Generator
from sqlalchemy import text
from sqlmodel import create_engine, Session, SQLModel
from app.config import settings
from app.models.db_models import Course, ProfessorReview, TimeSlot

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,       # Comprueba que la conexión está viva antes de usarla
    pool_recycle=300,         # Recicla conexiones descartándolas cada 5 minutos
    pool_size=10,             # Número máximo de conexiones permanentes en el pool
    max_overflow=10,          # Número máximo de conexiones extras si el pool se llena
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def run_migrations():
    """Ejecuta migraciones pendientes (columnas nuevas en tablas existentes)."""
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE source_file ADD COLUMN IF NOT EXISTS carrera VARCHAR(255)"
            ))
            conn.execute(text(
                "ALTER TABLE source_file ADD COLUMN IF NOT EXISTS facultad VARCHAR(255)"
            ))
            conn.execute(text(
                "ALTER TABLE source_file ADD COLUMN IF NOT EXISTS campus VARCHAR(255)"
            ))
            conn.execute(text(
                "ALTER TABLE source_file ADD COLUMN IF NOT EXISTS periodo VARCHAR(255)"
            ))
            conn.execute(text(
                "ALTER TABLE professor_review ADD COLUMN IF NOT EXISTS claridad INTEGER"
            ))
            conn.execute(text(
                "ALTER TABLE professor_review ADD COLUMN IF NOT EXISTS dificultad INTEGER"
            ))
            conn.execute(text(
                "ALTER TABLE professor_review ADD COLUMN IF NOT EXISTS recomendaria INTEGER"
            ))
            conn.execute(text(
                "ALTER TABLE professor_review ADD COLUMN IF NOT EXISTS materia_nombre VARCHAR(255)"
            ))
            for col in (
                "dominio_contenido", "metodologia", "justicia_evaluacion",
                "exigencia", "apoyo", "organizacion", "impacto",
            ):
                conn.execute(text(
                    f"ALTER TABLE professor_review ADD COLUMN IF NOT EXISTS {col} INTEGER"
                ))
            for col in (
                "justificacion_dominio", "justificacion_claridad", "justificacion_metodologia",
                "justificacion_justicia", "justificacion_exigencia", "justificacion_apoyo",
                "justificacion_organizacion", "justificacion_impacto", "comentario_general",
            ):
                conn.execute(text(
                    f"ALTER TABLE professor_review ADD COLUMN IF NOT EXISTS {col} TEXT"
                ))
    except Exception as e:
        # Si la tabla no existe, create_all la creara con todas las columnas
        if "does not exist" not in str(e).lower():
            raise


logger = logging.getLogger(__name__)

def init_db():
    retries = 5
    for i in range(retries):
        try:
            SQLModel.metadata.create_all(engine)
            run_migrations()
            break
        except Exception as e:
            if i < retries - 1:
                logger.warning(f"Esperando a la base de datos... (intento {i+1}/{retries})")
                time.sleep(2)
            else:
                logger.error("No se pudo conectar a la base de datos.")
                raise
