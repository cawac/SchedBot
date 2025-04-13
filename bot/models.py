from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Time, Date, BigInteger, CheckConstraint, Text, DateTime, PrimaryKeyConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    tg_id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="SET NULL"))

    group = relationship("Group")


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)


class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"))
    type = Column(String(25), nullable=False)
    auditorium = Column(String(20), nullable=True)

    subject = relationship("Subject")

    __table_args__ = (
        CheckConstraint("type IN ('Lecture', 'Practice')", name="lesson_type_check"),
    )


class LessonGroup(Base):
    __tablename__ = "lesson_groups"
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    lesson_date = Column(Date, nullable=False)
    lesson_number = Column(Integer, ForeignKey("lesson_time.lesson_number", ondelete="SET NULL"))
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"))

    __table_args__ = (
        PrimaryKeyConstraint("group_id", "lesson_date", "lesson_number"),
    )

    lesson = relationship("Lesson")
    group = relationship("Group")
    lesson_time = relationship("LessonTime", foreign_keys=[lesson_number])


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)


class LessonTime(Base):
    __tablename__ = "lesson_time"
    lesson_number = Column(Integer, primary_key=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    __table_args__ = (
        CheckConstraint("lesson_number BETWEEN 1 AND 7", name="lesson_number_check"),
    )
