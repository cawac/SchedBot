from collections import defaultdict
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
        entity_id = None
        with self.atomic() as session:
            entity = model(**kwargs)
            session.add(entity)
            session.flush()
            entity_id = entity.id

        logger_database.info(f"entity for model {model.__name__} with: {kwargs} created.")
        return entity_id

    def create_user(self, **kwargs) -> Base:
        return self.create_entity(User, **kwargs)

    def create_group(self, **kwargs) -> Base:
        return self.create_entity(Group, **kwargs)

    def create_lesson(self, **kwargs) -> Base:
        return self.create_entity(Lesson, **kwargs)

    def create_subject(self, **kwargs) -> Base:
        return self.create_entity(Subject, **kwargs)

    def create_lesson_time(self, **kwargs) -> Base:
        return self.create_entity(LessonTime, **kwargs)

    def create_lesson_and_add_groups(self, group_names: list, lesson_date: date, lesson_number: int, subject_name: str,
                                     lesson_type: str, auditorium: str = None):
        lesson_groups = None
        with self.atomic() as session:
            subject = session.query(Subject).filter(Subject.name == subject_name).first()
            subject_id = None

            if not subject:
                subject_id = self.create_entity(Subject, name=subject_name)
            else:
                subject_id = subject.id

            lesson_id = self.create_entity(Lesson, subject_id=subject_id, lesson_type=lesson_type, auditorium=auditorium,
                                        lesson_number=lesson_number, lesson_date=lesson_date)

            logger_database.info(f"Lesson created for subject {subject_id} of type {lesson_type}.")

            group_ids = session.scalars(
                select(Group.id).where(Group.name.in_(group_names))
            ).all()

            lesson_groups = [
                LessonGroup(
                    lesson_id=lesson_id,
                    group_id=group_id,
                )
                for group_id in group_ids
            ]

            session.add_all(lesson_groups)

        # logger_database.info(f"Lesson for groups: {group_ids} attached to lesson {lesson.id}.")
        return lesson_groups

    # Read
    def get_groups(self) -> Optional[List[type[Group]]]:
        return self.session().query(Group).all()

    def get_user_lessons_on_date(self, tg_id: int, searching_date: date):
        with self.atomic() as session:
            user = session.scalar(select(User).where(User.tg_id == tg_id))
            if not user:
                logger_database.info(f"User with tg_id {tg_id} not found.")
                return None

            stmt = (
                select(Lesson)
                .join(LessonGroup)
                .where(
                    and_(
                        LessonGroup.group_id == user.group_id,
                        Lesson.lesson_date == searching_date,
                    )
                )
                .order_by(Lesson.lesson_date.asc(), Lesson.lesson_number.asc())
            )

            lesson_groups = session.scalars(stmt).all()
            if not lesson_groups:
                logger_database.info(f"No lessons found for user {tg_id} for {searching_date}")
                return None

            lessons_by_date = [
                {
                    "lesson_number": lesson.lesson_number,
                    "lesson_type": lesson.lesson_type,
                    "lesson_start_time": f"{lesson.lesson_time.start_time.hour:02d}:{lesson.lesson_time.start_time.minute:02d}",
                    "lesson_end_time": f"{lesson.lesson_time.end_time.hour:02d}:{lesson.lesson_time.end_time.minute:02d}",
                    "subject_name": lesson.subject.name,
                }
                for lesson in lesson_groups
            ]

            # logger_database.info(
            #     f"Found {len(lessons_by_date)} lessons for user {tg_id} from {start_period} to {end_period}.")
            return lessons_by_date

    def get_user_lessons_on_period(
            self, tg_id: int, start_period: date, end_period: date
    ) -> Optional[List[Dict[str, any]]]:
        with self.atomic() as session:
            user = session.scalar(select(User).where(User.tg_id == tg_id))
            if not user:
                logger_database.info(f"User with tg_id {tg_id} not found.")
                return None

            stmt = (
                select(Lesson)
                .join(LessonGroup)
                .where(
                    and_(
                        LessonGroup.group_id == user.group_id,
                        and_(
                            Lesson.lesson_date >= start_period,
                            Lesson.lesson_date <= end_period
                        )
                    )
                )
                .order_by(Lesson.lesson_date.asc(), Lesson.lesson_number.asc())
            )

            lesson_groups = session.scalars(stmt).all()
            if not lesson_groups:
                logger_database.info(f"No lessons found for user {tg_id} from {start_period} to {end_period}.")
                return None

            lessons_by_date = defaultdict(list)
            for lesson in lesson_groups:
                date_key = lesson.lesson_date
                lesson_info = {
                    "lesson_number": lesson.lesson_number,
                    "lesson_type": lesson.lesson_type,
                    "lesson_start_time": f"{lesson.lesson_time.start_time.hour:02d}:{lesson.lesson_time.start_time.minute:02d}",
                    "lesson_end_time": f"{lesson.lesson_time.end_time.hour:02d}:{lesson.lesson_time.end_time.minute:02d}",
                    "subject_name": lesson.subject.name,
                }
                lessons_by_date[date_key].append(lesson_info)

            lessons_by_date = dict(lessons_by_date)

            # logger_database.info(
            #     f"Found {len(lessons_by_date)} lessons for user {tg_id} from {start_period} to {end_period}.")
            return lessons_by_date

    # Update
    def attach_user_to_group(self, tg_id: int, group_name: str) -> None:
        with self.atomic() as session:
            user = session.scalar(select(User).where(User.tg_id == tg_id))
            group = session.scalar(select(Group).where(Group.name == group_name))

            if not user:
                self.create_entity(User, tg_id=tg_id)

            if not group:
                logger_database.info(f"Group {group_name} not found.")
                return None

            user.group_id = group.id
        logger_database.info(f"User {tg_id} attached to group.")
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
