"""Configuración de la aplicación."""
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Variables de entorno y configuración."""

    app_name: str = "Schedule Maker API"
    debug: bool = False
    upload_dir: Path = Path("uploads")
    data_dir: Path = Path("data")
    max_upload_mb: int = 20
    database_url: str = "postgresql://user:password@localhost:5432/schedule_db"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_prefix = "SCHEDULE_"
        env_file = ".env"


settings = Settings()
