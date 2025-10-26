from sqlalchemy import (
    Integer, String, ForeignKey,
    Time, Date, CheckConstraint, Column
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.subject import Subject


class LessonGroup(Base):
    __tablename__ = "group_lesson"

    group_id = Column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    lesson_id = Column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)

    # связи
    lesson = relationship("Lesson", back_populates="groups")
    group = relationship("Group", back_populates="lessons")


class LessonTime(Base):
    __tablename__ = 'lesson_time'

    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)  # ???
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)

    __table_args__ = (
        CheckConstraint('lesson_number BETWEEN 1 AND 7', name='lesson_number_check'),
    )

lesson_type_enum = postgresql.ENUM(
    "UNKNOWN", "LECTURE", "PRACTICE", "SEMINAR", "LAB", "EXAM",
    name="lesson_type",
    create_type=True
)

class Lesson(Base):
    __tablename__ = "lessons"

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    lesson_type: Mapped[str] = mapped_column(lesson_type_enum, nullable=True)
    auditorium: Mapped[str] = mapped_column(String(20), nullable=True)
    lesson_number: Mapped[int] = mapped_column(ForeignKey("lesson_time.lesson_number", ondelete="SET NULL"), nullable=True)
    lesson_date: Mapped[Date] = mapped_column(Date, nullable=False)

    subject: Mapped["Subject"] = relationship()
    lesson_time: Mapped["LessonTime"] = relationship("LessonTime", foreign_keys=[lesson_number])
    groups: Mapped[list["LessonGroup"]] = relationship("LessonGroup", back_populates="lesson")