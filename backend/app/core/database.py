from typing import Generator

from sqlmodel import create_engine, Session, SQLModel
from app.config import settings
from app.models.db_models import Course, TimeSlot

engine = create_engine(settings.database_url, echo=settings.debug)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
