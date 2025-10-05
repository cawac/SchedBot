import enum

from sqlalchemy import (
    Integer, String, ForeignKey,
    Time, Date, CheckConstraint, Enum, Table, Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.subject import Subject


LessonGroup = Table(
    "group_lesson",
    Base.metadata,
    Column("group_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    Column("lesson_id", ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
)


class LessonTime(Base):
    __tablename__ = 'lesson_time'

    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)  # ???
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)

    __table_args__ = (
        CheckConstraint('lesson_number BETWEEN 1 AND 7', name='lesson_number_check'),
    )


class Lesson(Base):
    __tablename__ = 'lessons'

    class LessonType(enum.Enum):
        UNKNOWN = 'unknown'
        LECTURE = 'lecture'
        PRACTICE = 'practice'
        SEMINAR = 'seminar'
        LAB = 'lab'
        EXAM = 'exam'

    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False) # ???
    lesson_type: Mapped[LessonType] = mapped_column(
        Enum(LessonType, name='lesson_type'), nullable=False
    )
    auditorium: Mapped[str] = mapped_column(String(20), nullable=True)
    lesson_number: Mapped[LessonTime] = mapped_column(Integer, ForeignKey('lesson_time.lesson_number', ondelete='SET NULL'))
    lesson_date: Mapped[Date] = mapped_column(Date, nullable=False)

    subject: Mapped[Subject] = relationship()
    lesson_time = relationship('LessonTime', foreign_keys=[lesson_number])
