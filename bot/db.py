from datetime import time, date, datetime, timedelta
from operator import and_
from typing import Any, List, Dict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, InstrumentedAttribute
from sqlalchemy.exc import IntegrityError

from models import User, Group, LessonGroup, Lesson, LessonTime, Subject, Base
import logger
import logging
from config import DATABASE_URL


logger_database = logging.getLogger("database")


class DBManager:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    # Create
    def create_user(self, tg_id: int, group_id: int = None) -> None:
        session = self.Session()
        try:
            user = User(tg_id=tg_id, group_id=group_id)
            session.add(user)
            session.commit()
            logger_database.info(f"User {tg_id} created.")
        except IntegrityError:
            session.rollback()
            logger_database.info(f"User {tg_id} already exists.")
        except Exception as e:
            session.rollback()
            logger_database.error(f"Creating user '{tg_id}': {str(e)}")
        finally:
            session.close()

    def create_group(self, name: str) -> None:
        session = self.Session()
        try:
            group = Group(name=name)
            session.add(group)
            session.commit()
            logger_database.info(f"Group '{name}' created.")
        except IntegrityError:
            session.rollback()
            logger_database.info(f"Group '{name}' already exists.")
        except Exception as e:
            session.rollback()
            logger_database.error(f"Creating group '{name}': {str(e)}")
        finally:
            session.close()

    def create_lesson(self, subject_id: int, type_of_lesson: str, auditorium: str = None) -> None:
        session = self.Session()
        try:
            lesson = Lesson(subject_id=subject_id, type=type_of_lesson, auditorium=auditorium)
            session.add(lesson)
            session.commit()
            logger_database.info(f"Lesson created for subject {subject_id} of type {type_of_lesson}.")
        # except IntegrityError:
        #     session.rollback()
        #     logger.info(f"Could not create lesson {subject_id} of type {type_of_lesson}.")
        except Exception as e:
            session.rollback()
            logger_database.error(f"Creating lesson '{subject_id}' : {str(e)}")
        finally:
            session.close()

    def create_subject(self, subject_name: str) -> None:
        session = self.Session()
        try:
            subject = Subject(name=subject_name)
            session.add(subject)
            session.commit()
            logger_database.info(f"Subject '{subject_name}' created.")
        except IntegrityError:
            session.rollback()
            logger_database.info(f"Subject {subject_name} already exists.")
        except Exception as e:
            session.rollback()
            logger_database.error(f"Creating subject '{subject_name}': {str(e)}")
        finally:
            session.close()

    def create_lesson_time(self, lesson_number: int, start_time: time, end_time: time) -> None:
        session = self.Session()
        try:
            lesson_time = LessonTime(lesson_number=lesson_number, start_time=start_time, end_time=end_time)
            session.add(lesson_time)
            session.commit()
            logger_database.info(f"Lesson time for lesson number {lesson_number} created, from {start_time} to {end_time}.")
        except IntegrityError:
            session.rollback()
            logger_database.info(f"Lesson number {lesson_number} already exists.")
        except Exception as e:
            session.rollback()
            logger_database.error(f"Creating lesson time for lesson number {lesson_number}: {str(e)}")
        finally:
            session.close()

    def create_lesson_and_add_groups(self, group_names: list, lesson_date: date, lesson_number: int, subject_name: str,
                                     lesson_type: str, auditorium: str = None) -> None:
        session = self.Session()
        try:
            subject = session.query(Subject).filter(Subject.name == subject_name).first()

            if not subject:
                logger_database.info(f"Subject '{subject_name}' not found.")
                return

            lesson = Lesson(subject_id=subject.id, type=lesson_type, auditorium=auditorium)
            session.add(lesson)
            session.commit()

            logger_database.info(f"Lesson created for subject {subject.id} of type {lesson_type}.")

            group_ids = []
            for group_name in group_names:
                group = session.query(Group).filter(Group.name == group_name).first()
                if group:
                    group_ids.append(group.id)
                else:
                    continue

            for group_id in group_ids:
                lesson_group = LessonGroup(
                    lesson_id=lesson.id,
                    group_id=group_id,
                    lesson_date=lesson_date,
                    lesson_number=lesson_number
                )
                session.add(lesson_group)

            session.commit()

            for group_id in group_ids:
                logger_database.info(f"Group {group_id} attached to lesson {lesson.id}.")
        except IntegrityError:
            session.rollback()
            # TODO:
        except Exception as e:
            session.rollback()
            logger_database.error(f"Creating lesson and adding groups: {str(e)}")
        finally:
            session.close()

    def get_user_lessons_on_date(self, tg_id: int, lesson_date: date) -> list[dict[str, InstrumentedAttribute | Any]] | None:
        session = self.Session()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()

            if not user:
                logger_database.info(f"User with tg_id {tg_id} not found.")
                return None

            lessons = session.query(LessonGroup).join(Lesson).join(Group).join(LessonTime).filter(
                and_(
                    LessonGroup.lesson_date == lesson_date.strftime('%Y-%m-%d'),
                    LessonGroup.group_id == user.group_id
                )
            ).order_by(LessonGroup.lesson_number.asc()).all()

            if not lessons:
                logger_database.info(f"No lessons found for user {tg_id} on {lesson_date}.")
                return []

            logger_database.info(f"Found {len(lessons)} lessons for user {tg_id} on {lesson_date}.")

            lesson_details = []
            for lesson in lessons:
                lesson_info = {
                    "lesson_date": lesson.lesson_date,
                    "lesson_number": lesson.lesson_number,
                    "subject_name": lesson.lesson.subject.name,
                    "lesson_type": lesson.lesson.type,
                    "lesson_start_time": lesson.lesson_time.start_time.strftime('%H:%M'),
                    "lesson_end_time": lesson.lesson_time.end_time.strftime('%H:%M'),
                }
                lesson_details.append(lesson_info)

            return lesson_details

        except Exception as e:
            session.rollback()
            logger_database.error(f"Fetching lessons for user {tg_id} on {lesson_date}: {str(e)}")
            return None
        finally:
            session.close()

    def get_user_lessons_on_period(self, tg_id: int, start_period: date, end_period: date) -> List[List[Dict[str, InstrumentedAttribute | Any]]]:
        session = self.Session()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()

            if not user:
                logger_database.info(f"User with tg_id {tg_id} not found.")
                return None

            current_date = start_period
            lessons_on_dates: list = []
            while current_date <= end_period:
                lessons_on_date = self.get_user_lessons_on_date(tg_id, current_date)
                lessons_on_dates.append(lessons_on_date)
                current_date += timedelta(days=1)

            if not any(lessons_on_dates):
                logger_database.info(f"No lessons found for user {tg_id} from {start_period} to {end_period}.")
                return []

            logger_database.info(f"Found lessons for user {tg_id} from {start_period} to {end_period}.")
            return lessons_on_dates

        except Exception as e:
            session.rollback()
            logger_database.error(f"Fetching lessons for user {tg_id} from {start_period} to {end_period}: {str(e)}")
            return None
        finally:
            session.close()

    def get_user_lessons_on_period_2(self, tg_id: int, start_period: date, amount_of_days: int = 1) -> List[List[Dict[str, InstrumentedAttribute | Any]]]:
        session = self.Session()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()

            if not user:
                logger_database.info(f"User with tg_id {tg_id} not found.")
                return None

            current_date = start_period
            lessons_on_dates: list = []
            processed_days = 0
            while processed_days <= amount_of_days:
                lessons_on_date = self.get_user_lessons_on_date(tg_id, current_date)
                lessons_on_dates.append(lessons_on_date)
                current_date += timedelta(days=1)
                processed_days += 1

            if not any(lessons_on_dates):
                logger_database.info(f"No lessons found for user {tg_id} from {start_period} for amount of days {amount_of_days + 1}.")
                return []

            logger_database.info(f"Found lessons for user {tg_id} from {start_period} for amount of days {amount_of_days + 1}.")
            return lessons_on_dates

        except Exception as e:
            session.rollback()
            logger_database.error(f"Fetching lessons for user {tg_id} from {start_period} for amount of days {amount_of_days + 1}: {str(e)}")
            return None
        finally:
            session.close()

    def get_user_lessons_on_period_3(self, tg_id: int, start_period: date, amount_of_days: int = 1) -> Dict[date, List[Dict[str, InstrumentedAttribute | Any]]] | None:
        session = self.Session()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()

            if not user:
                logger_database.info(f"User with tg_id {tg_id} not found.")
                return None

            current_date = start_period
            lessons_on_dates: dict = dict()
            processed_days = 0
            while processed_days <= amount_of_days:
                lessons_on_date = self.get_user_lessons_on_date(tg_id, current_date)
                lessons_on_dates[current_date] = lessons_on_date
                current_date += timedelta(days=1)
                processed_days += 1

            if len(lessons_on_dates) == 0:
                logger_database.info(f"No lessons found for user {tg_id} from {start_period} for amount of days {amount_of_days + 1}.")
                return None

            logger_database.info(f"Found lessons for user {tg_id} from {start_period} for amount of days {amount_of_days + 1}.")
            return lessons_on_dates

        except Exception as e:
            session.rollback()
            logger_database.error(f"Fetching lessons for user {tg_id} from {start_period} for amount of days {amount_of_days + 1}: {str(e)}")
            return None
        finally:
            session.close()

    def attach_user_to_group(self, tg_id: int, group_name: str) -> str:
        session = self.Session()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()

            if not user:
                logger_database.info(f"User {tg_id} not found.")
                return "User not found."

            group = session.query(Group).filter(Group.name == group_name).first()

            if not group:
                logger_database.info(f"Group {group_name} not found.")
                return f"Group {group_name} not found."

            user.group_id = group.id
            session.commit()
            logger_database.info(f"User {tg_id} attached to group '{group.name}'.")
            return f"Attached to group '{group.name}'."

        except Exception as e:
            session.rollback()
            logger_database.error(f"Attaching user {tg_id} to group {group_name}: {str(e)}")
            return "Something went wrong write to @cawa0007"
        finally:
            session.close()

    def set_default(self):
        lesson_times = [
            (1, time(9, 0), time(10, 30)),
            (2, time(10, 40), time(12, 10)),
            (3, time(12, 20), time(13, 50)),
            (4, time(14, 20), time(15, 50)),
            (5, time(16, 0), time(17, 30)),
            (6, time(18, 0), time(19, 30)),
            (7, time(19, 50), time(21, 20))
        ]
        for lesson_time in lesson_times:
            self.create_lesson_time(lesson_time[0], lesson_time[1], lesson_time[2])

        self.subjects = [
            "DesignPatterns",
            "Algorithms and DS",
            "ProbTheory&Stats",
            "ProbTheory&Stats",
            "OS Software",
            "SQL&DataProc",
            "Multythread. JA",
            "Modern JS WebDev",
            "Automated testing",
            "Multythread. C#",
            "IP Law Basics",
            "WebDev JS",
            "Intro to DT",
            "Disc Math",
            "OOP Java",
            "English",
            "Func Sftw Testing",
            "High Math",
            "CloudTech",
            "Cryptogr&Blockchain",
            "Моbile Dev Kotlin",
            "UX/UI design",
            "Team project",
            "Моbile Dev React Native",
            "Project Planning Method",
            "Machine Learning",
            "BA basics",
            "WebDev with .NET",
            "PM basics"
        ]

        for subject_name in self.subjects:
            self.create_subject(subject_name)

    def delete_yesterday_lessons(self) -> None:
        session = self.Session()
        try:
            yesterday = (datetime.now().date() - timedelta(days=1))

            deleted_count = session.query(LessonGroup).filter(
                LessonGroup.lesson_date == yesterday
            ).delete(synchronize_session=False)

            session.commit()
            logger_database.info(f"Deleted {deleted_count} lessons from {yesterday}.")
        except Exception as e:
            session.rollback()
            logger_database.error(f"Error deleting yesterday's lessons: {str(e)}")
        finally:
            session.close()

    def get_groups(self):
        session = self.Session()
        try:
            groups = session.query(Group).all()
            return groups
        except Exception as e:
            session.rollback()
            logger_database.error(f"Error at getting all groups {e}")
            return []
        finally:
            session.close()


database: DBManager = DBManager(database_url=DATABASE_URL)
