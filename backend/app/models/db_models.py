from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from app.models.schemas import DayEnum
from datetime import time, datetime


class SourceFile(SQLModel, table=True):
    __tablename__ = "source_file"
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    file_hash: str = Field(index=True, unique=True)
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    courses: List["Course"] = Relationship(back_populates="source_file")


class Course(SQLModel, table=True):
    __tablename__ = "course"
    id: Optional[int] = Field(default=None, primary_key=True)
    nrc: str = Field(index=True)
    course_code: str
    group_code: str
    subject_name: str
    professor: Optional[str] = None
    credits: Optional[int] = None
    
    source_file_id: Optional[int] = Field(default=None, foreign_key="source_file.id")
    source_file: Optional[SourceFile] = Relationship(back_populates="courses")

    time_slots: List["TimeSlot"] = Relationship(back_populates="course")


class TimeSlot(SQLModel, table=True):
    __tablename__ = "time_slot"
    id: Optional[int] = Field(default=None, primary_key=True)
    day: DayEnum
    start_time: time
    end_time: time
    classroom: Optional[str] = None
    
    course_id: Optional[int] = Field(default=None, foreign_key="course.id")
    course: Optional[Course] = Relationship(back_populates="time_slots")
