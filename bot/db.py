from datetime import time, date, datetime, timedelta
from operator import and_
from typing import List, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, InstrumentedAttribute
from sqlalchemy.exc import IntegrityError

from models import *
from logger import logger
from config import tz


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
            logger.info(f"User {tg_id} created.")
        except IntegrityError:
            session.rollback()
            logger.error(f"User {tg_id} already exists.")
        except Exception as e:
            session.rollback()
            logger.error(f"Creating user '{tg_id}': {str(e)}")
        finally:
            session.close()

    def create_group(self, name: str) -> None:
        session = self.Session()
        try:
            group = Group(name=name)
            session.add(group)
            session.commit()
            logger.info(f"Group '{name}' created.")
        except IntegrityError:
            session.rollback()
            logger.error(f"Group '{name}' already exists.")
        finally:
            session.close()

    def create_lesson(self, subject_id: int, type_of_lesson: str) -> None:
        session = self.Session()
        try:
            lesson = Lesson(subject_id=subject_id, type=type_of_lesson)
            session.add(lesson)
            session.commit()
            logger.info(f"Lesson created for subject {subject_id} of type {type_of_lesson}.")
        except IntegrityError:
            session.rollback()
            logger.error(f"Error: Could not create lesson.")
        finally:
            session.close()

    def create_subject(self, subject_name: str) -> None:
        session = self.Session()
        try:
            subject = Subject(name=subject_name)
            session.add(subject)
            session.commit()
            logger.info(f"Subject '{subject_name}' created.")
        except IntegrityError:
            session.rollback()
            logger.error(f"Subject {subject_name} already exists.")
        except Exception as e:
            session.rollback()
            logger.error(f"Creating subject '{subject_name}': {str(e)}")
        finally:
            session.close()

    def create_lesson_time(self, lesson_number: int, start_time: time, end_time: time) -> None:
        session = self.Session()
        try:
            lesson_time = LessonTime(lesson_number=lesson_number, start_time=start_time, end_time=end_time)
            session.add(lesson_time)
            session.commit()
            logger.info(f"Lesson time for lesson number {lesson_number} created, from {start_time} to {end_time}.")
        except IntegrityError:
            session.rollback()
            logger.error(f"Lesson number {lesson_number} already exists.")
        except Exception as e:
            session.rollback()
            logger.error(f"Creating lesson time for lesson number {lesson_number}: {str(e)}")
        finally:
            session.close()

    def create_lesson_and_add_groups(self, group_names: list, lesson_date: date, lesson_number: int, subject_name: str,
                                     lesson_type: str) -> None:
        session = self.Session()
        try:
            subject = session.query(Subject).filter(Subject.name == subject_name).first()

            if not subject:
                logger.error(f"Subject '{subject_name}' not found.")
                return

            lesson = Lesson(subject_id=subject.id, type=lesson_type)
            session.add(lesson)
            session.commit()

            logger.info(f"Lesson created for subject {subject.id} of type {lesson_type}.")

            group_ids = []
            for group_name in group_names:
                group = session.query(Group).filter(Group.name == group_name).first()
                if group:
                    group_ids.append(group.id)
                    logger.info(f"Group '{group_name}' found with ID {group.id}.")
                else:
                    logger.error(f"Group '{group_name}' not found.")
                    continue

            localized_data = tz.localize(lesson_date)
            for group_id in group_ids:
                lesson_group = LessonGroup(
                    lesson_id=lesson.id,
                    group_id=group_id,
                    lesson_date=localized_data,
                    lesson_number=lesson_number
                )
                session.add(lesson_group)

            session.commit()

            for group_id in group_ids:
                logger.info(f"Group {group_id} attached to lesson {lesson.id}.")
        except Exception as e:
            session.rollback()
            logger.error(f"Creating lesson and adding groups: {str(e)}")
        finally:
            session.close()

    def get_user_lessons_on_date(self, tg_id: int, lesson_date: date) -> list[dict[str, InstrumentedAttribute | Any]] | None:
        session = self.Session()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()

            if not user:
                logger.error(f"User with tg_id {tg_id} not found.")
                return None

            lessons = session.query(LessonGroup).join(Lesson).join(Group).join(LessonTime).filter(
                and_(
                    LessonGroup.lesson_date == lesson_date.strftime('%Y-%m-%d'),
                    LessonGroup.group_id == user.group_id
                )
            ).order_by(LessonGroup.lesson_number.asc()).all()

            if not lessons:
                logger.info(f"No lessons found for user {tg_id} on {lesson_date}.")
                return []

            logger.info(f"Found {len(lessons)} lessons for user {tg_id} on {lesson_date}.")

            lesson_details = []
            for lesson in lessons:
                lesson_info = {
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
            logger.error(f"Fetching lessons for user {tg_id} on {lesson_date}: {str(e)}")
            return None
        finally:
            session.close()

    def attach_user_to_group(self, tg_id: int, group_name: str) -> str:
        session = self.Session()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()

            if not user:
                logger.error(f"User {tg_id} not found.")
                return f"User not found."

            group = session.query(Group).filter(Group.name == group_name).first()

            if not group:
                logger.error(f"Group {group_name} not found.")
                return f"Group {group_name} not found."

            user.group_id = group.id
            session.commit()
            logger.info(f"User {tg_id} attached to group '{group.name}'.")
            return f"Attached to group '{group.name}'."

        except Exception as e:
            session.rollback()
            logger.error(f"Attaching user {tg_id} to group {group_name}: {str(e)}")
            return f"Something went wrong write to @cawa0007"
        finally:
            session.close()

    def set_default(self):
        lesson_times = [
            (1, time(9, 0), time(10, 30)),  # Lesson 1: 9:00 - 10:30
            (2, time(10, 40), time(12, 10)),  # Lesson 2: 10:40 - 12:10
            (3, time(12, 20), time(13, 50)),  # Lesson 3: 12:20 - 13:50
            (4, time(14, 20), time(15, 50)),  # Lesson 4: 14:20 - 15:50
            (5, time(16, 0), time(17, 30)),  # Lesson 5: 16:00 - 17:30
            (6, time(18, 0), time(19, 30)),  # Lesson 6: 18:00 - 19:30
            (7, time(19, 50), time(21, 20))  # Lesson 7: 19:50 - 21:20
        ]
        for lesson_time in lesson_times:
            self.create_lesson_time(lesson_time[0], lesson_time[1], lesson_time[2])

        subjects = [
            "Algorithms and DS",
            "ProbTheory&Stats",
            "DesignPatterns",
            "OS Software",
            "Multythread. C#",
            "SQL&DataProc", 
            "Modern JS WebDev",
            "Automated testing",
            "IP Law Basics",
        ]
        for subject_name in subjects:
            self.create_subject(subject_name)

    def delete_yesterdays_lessons(self) -> None:
        session = self.Session()
        try:
            yesterday = (datetime.now().date() - timedelta(days=1))

            deleted_count = session.query(LessonGroup).filter(
                LessonGroup.lesson_date == yesterday
            ).delete(synchronize_session=False)

            session.commit()
            logger.info(f"Deleted {deleted_count} lessons from {yesterday}.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting yesterday's lessons: {str(e)}")
        finally:
            session.close()