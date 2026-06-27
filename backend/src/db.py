from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from operator import and_
from typing import Any, List, Dict, Optional

from sqlalchemy import create_engine, select
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from models.base import Base
from utils.logger import logger
import logging
from config import DATABASE_URL
from models.group import Group
from models.lesson import Lesson, LessonTime, LessonGroup
from models.subject import Subject
from models.user import User
from models.auditorium import Auditorium
from models.user_action import UserAction

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

        return lesson_groups

    def get_groups(self) -> Optional[List[Group]]:
        with self.atomic() as session:
            groups = session.scalars(select(Group)).all()
            if not groups:
                logger_database.info("No groups found")
                return []
            for group in groups:
                _ = group.id
                _ = group.name
                session.expunge(group)
            logger_database.info(f"Loaded {len(groups)} groups")
            return groups

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
                        Lesson.lesson_date >= start_period,
                        Lesson.lesson_date <= end_period
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

            return lessons_by_date

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

    def get_all_buildings(self) -> List[str]:
        """Get list of all buildings."""
        with self.atomic() as session:
            buildings = session.query(Auditorium.building).distinct().all()
            return [b[0] for b in buildings]

    def get_auditoriums_by_building(self, building: str) -> List[Auditorium]:
        """Filter auditoriums by building."""
        with self.atomic() as session:
            auditoriums = session.query(Auditorium).filter(Auditorium.building == building).all()
            for aud in auditoriums:
                _ = aud.id
                _ = aud.name
                _ = aud.building
                _ = aud.floor
                _ = aud.capacity
                _ = aud.type
                session.expunge(aud)
            return auditoriums

    def get_auditoriums_by_type(self, aud_type: str) -> List[Auditorium]:
        """Filter auditoriums by type."""
        with self.atomic() as session:
            auditoriums = session.query(Auditorium).filter(Auditorium.type == aud_type).all()
            for aud in auditoriums:
                _ = aud.id
                _ = aud.name
                _ = aud.building
                _ = aud.floor
                _ = aud.capacity
                _ = aud.type
                session.expunge(aud)
            return auditoriums

    def get_auditorium_types(self) -> List[str]:
        """Get list of all auditorium types."""
        with self.atomic() as session:
            types = session.query(Auditorium.type).distinct().all()
            return [t[0] for t in types]

    def get_free_auditoriums_at_lesson(
        self,
        lesson_number: int,
        searching_date: date,
        building: str = None,
        auditorium_type: str = None
    ) -> List[Dict[str, Any]]:
        """Find free auditoriums at a specific lesson number on a specific date."""
        with self.atomic() as session:
            occupied_query = (
                session.query(Lesson.auditorium_id)
                .filter(
                    and_(
                        Lesson.lesson_date == searching_date,
                        Lesson.lesson_number == lesson_number,
                        Lesson.auditorium_id.isnot(None)
                    )
                )
            )
            occupied_ids = [row[0] for row in occupied_query.all()]

            query = session.query(Auditorium).filter(Auditorium.id.notin_(occupied_ids))

            if building:
                query = query.filter(Auditorium.building == building)

            if auditorium_type:
                query = query.filter(Auditorium.type == auditorium_type)

            auditoriums = query.order_by(Auditorium.building, Auditorium.floor, Auditorium.number).all()

            return [
                {
                    "name": aud.name,
                    "number": aud.number,
                    "building": aud.building,
                    "floor": aud.floor,
                    "capacity": aud.capacity,
                    "type": aud.type
                }
                for aud in auditoriums
            ]

    def log_user_action(
        self,
        user_id: int,
        action_type: str,
        command_name: str = None,
        metadata: dict = None
    ) -> int:
        """Log user action to user_actions table."""
        with self.atomic() as session:
            action = UserAction(
                user_id=user_id,
                action_type=action_type,
                command_name=command_name,
                action_metadata=metadata
            )
            session.add(action)
            session.flush()
            return action.id

    def get_user_by_tg_id(self, tg_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        with self.atomic() as session:
            user = session.scalar(select(User).where(User.tg_id == tg_id))
            if user:
                _ = user.id
                _ = user.tg_id
                _ = user.group_id
                _ = user.is_admin
                session.expunge(user)
            return user

    def get_user_stats_this_week(self, tg_id: int) -> Optional[Dict[str, Any]]:
        """
        Return user statistics for current week (Monday to Sunday):
        - total_lessons
        - labs, practices, lectures
        - workload_by_day (dict date -> count)
        """
        with self.atomic() as session:
            user = session.scalar(select(User).where(User.tg_id == tg_id))
            if not user or not user.group_id:
                return None

            today = datetime.now().date()
            weekday = today.weekday()
            week_start = today - timedelta(days=weekday)
            week_end = week_start + timedelta(days=6)

            stmt = (
                select(Lesson)
                .join(LessonGroup)
                .where(
                    and_(
                        LessonGroup.group_id == user.group_id,
                        Lesson.lesson_date >= week_start,
                        Lesson.lesson_date <= week_end
                    )
                )
            )

            lessons = session.scalars(stmt).all()

            if not lessons:
                return {
                    "total_lessons": 0,
                    "lectures": 0,
                    "practices": 0,
                    "labs": 0,
                    "workload_by_day": {}
                }

            total_lessons = len(lessons)
            lectures = sum(1 for l in lessons if l.lesson_type == "LECTURE")
            practices = sum(1 for l in lessons if l.lesson_type == "PRACTICE")
            labs = sum(1 for l in lessons if l.lesson_type == "LAB")

            workload_by_day = defaultdict(int)
            for lesson in lessons:
                workload_by_day[lesson.lesson_date] += 1

            return {
                "total_lessons": total_lessons,
                "lectures": lectures,
                "practices": practices,
                "labs": labs,
                "workload_by_day": dict(workload_by_day)
            }

    def get_dau_wau_mau(self) -> Dict[str, int]:
        """
        Return DAU/WAU/MAU from user_actions:
        - DAU: distinct user_id today
        - WAU: distinct user_id last 7 days
        - MAU: distinct user_id last 30 days
        """
        with self.atomic() as session:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            dau_query = (
                select(UserAction.user_id)
                .distinct()
                .where(UserAction.timestamp >= datetime.combine(today, datetime.min.time()))
            )
            dau = len(session.scalars(dau_query).all())

            wau_query = (
                select(UserAction.user_id)
                .distinct()
                .where(UserAction.timestamp >= datetime.combine(week_ago, datetime.min.time()))
            )
            wau = len(session.scalars(wau_query).all())

            mau_query = (
                select(UserAction.user_id)
                .distinct()
                .where(UserAction.timestamp >= datetime.combine(month_ago, datetime.min.time()))
            )
            mau = len(session.scalars(mau_query).all())

            return {
                "dau": dau,
                "wau": wau,
                "mau": mau
            }

    def get_most_used_commands(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get top commands from last N days."""
        with self.atomic() as session:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = (
                session.query(
                    UserAction.command_name,
                    sa.func.count(UserAction.id).label('count')
                )
                .where(
                    and_(
                        UserAction.timestamp >= cutoff_date,
                        UserAction.command_name.isnot(None)
                    )
                )
                .group_by(UserAction.command_name)
                .order_by(sa.text('count DESC'))
                .limit(10)
            )

            results = query.all()
            return [
                {"command": row[0], "count": row[1]}
                for row in results
            ]


database_manager = DBManager(database_url=DATABASE_URL)
