from contextlib import contextmanager
from datetime import time, date, datetime, timedelta
from operator import and_
from typing import Any, List, Dict, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, InstrumentedAttribute, joinedload
from sqlalchemy.exc import IntegrityError

from models.base import Base
from utils.logger import logger
import logging
from config import DATABASE_URL
from models.group import Group
from models.lesson import Lesson, LessonTime, LessonGroup
from models.subject import Subject
from models.user import User

logger_database = logging.getLogger("database")


class DBManager:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url)
        self.session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def atomic(self):
        session = self.session()
        try:
            yield session
            session.commit()

        except IntegrityError as e:
            session.rollback()
            logger.error(f"Integrity error: {e}")

        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error: {e}")

        finally:
            session.close()

    # Create
    def create_entity(self, model, **kwargs) -> Base:
        entity = None
        with self.atomic() as session:
            entity = model(**kwargs)
            session.add(entity)

        logger_database.info(f"entity for model {model.__name__} with: {kwargs} created.")
        return entity

    def create_user(self, **kwargs) -> Base:
        return self.create_entity(User, **kwargs)

    def create_group(self, **kwargs) -> None:
        return self.create_entity(Group, **kwargs)

    def create_lesson(self, **kwargs) -> None:
        return self.create_entity(Lesson, **kwargs)

    def create_subject(self, **kwargs) -> None:
        return self.create_entity(Subject, **kwargs)

    def create_lesson_time(self, **kwargs) -> None:
        return self.create_entity(LessonTime, **kwargs)

    def create_lesson_and_add_groups(self, group_names: list, lesson_date: date, lesson_number: int, subject_name: str,
                                     lesson_type: str, auditorium: str = None):
        lesson_groups = None
        with self.atomic() as session:
            subject = session.query(Subject).filter(Subject.name == subject_name).first()

            if not subject:
                logger_database.info(f"Subject '{subject_name}' not found.")
                return None

            lesson = self.create_entity(Lesson, subject_id=subject.id, lesson_type=lesson_type, auditorium=auditorium,
                                        lesson_number=lesson_number, lesson_date=lesson_date)

            logger_database.info(f"Lesson created for subject {subject.id} of type {lesson_type}.")

            group_ids = session.scalars(
                select(Group.id).where(Group.name.in_(group_names))
            ).all()

            lesson_groups = [
                LessonGroup(
                    lesson_id=lesson.id,
                    group_id=group_id,
                )
                for group_id in group_ids
            ]

            session.add_all(lesson_groups)

        logger_database.info(f"Lesson for groups: {group_ids} attached to lesson {lesson.id}.")
        return lesson_groups

    # Read
    def get_groups(self) -> Optional[List[type[Group]]]:
        return self.session().query(Group).all()

    def get_user_lessons_on_period(
            self, tg_id: int, start_period: date, end_period: date
    ) -> Optional[List[Dict[str, any]]]:
        with self.atomic() as session:
            user = session.scalar(select(User).where(User.tg_id == tg_id))
            if not user:
                logger_database.info(f"User with tg_id {tg_id} not found.")
                return None

            stmt = (
                select(LessonGroup)
                .join(Lesson)
                .join(LessonTime)
                .options(
                    joinedload(LessonGroup.lesson).joinedload(Lesson.subject),
                    joinedload(LessonGroup.lesson_time)
                )
                .where(
                    and_(
                        LessonGroup.group_id == user.group_id,
                        and_(
                            Lesson.lesson_date <= end_period,
                            Lesson.lesson_date >= start_period,
                        )
                    )
                )
                .order_by(Lesson.lesson_date.asc(), LessonGroup.lesson_number.asc())
            )

            lesson_groups = session.scalars(stmt).all()
            if not lesson_groups:
                logger_database.info(f"No lessons found for user {tg_id} from {start_period} to {end_period}.")
                return None

            lesson_details = [
                {
                    "lesson_date": lg.lesson.lesson_date,
                    "lesson_number": lg.lesson.lesson_number,
                    "subject_name": lg.lesson.subject.name,
                    "lesson_type": lg.lesson.lesson_type,
                    "lesson_start_time": lg.lesson.lesson_time.start_time.strftime("%H:%M"),
                    "lesson_end_time": lg.lesson.lesson_time.end_time.strftime("%H:%M"),
                }
                for lg in lesson_groups
            ]

            logger_database.info(
                f"Found {len(lesson_details)} lessons for user {tg_id} from {start_period} to {end_period}.")
            return lesson_details

    # Update
    def attach_user_to_group(self, tg_id: int, group_name: str) -> None:
        with self.atomic() as session:
            user = session.scalar(select(User).where(User.tg_id == tg_id))
            group = session.scalar(select(Group).where(Group.name == group_name))

            if not user:
                logger_database.info(f"User {tg_id} not found.")
                return None

            if not group:
                logger_database.info(f"Group {group_name} not found.")
                return None

            user.group_id = group.id
        logger_database.info(f"User {tg_id} attached to group {group.name}.")
        return None

    # Delete
    def delete_lessons_before_date(self, date: date) -> int:
        deleted_count = 0
        with self.atomic() as session:
            deleted_count = (
                session.query(Lesson)
                .filter(Lesson.lesson_date < date)
                .delete(synchronize_session=False)
            )

        logger_database.info(f"Deleted {deleted_count} lessons before {date}.")
        return deleted_count


database_manager = DBManager(database_url=DATABASE_URL)
