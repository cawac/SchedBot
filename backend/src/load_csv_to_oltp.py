"""
Reenterable CSV loader for OLTP database.
Loads data from CSV files without creating duplicates.
"""
import csv
import logging
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.base import Base
from models.group import Group
from models.subject import Subject
from models.auditorium import Auditorium
from models.lesson import LessonTime
from datetime import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CSVLoader:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def load_groups(self, csv_path: str):
        """Load groups from CSV, checking for duplicates by name."""
        session = self.Session()
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                loaded_count = 0
                skipped_count = 0

                for row in reader:
                    # Check if group exists
                    existing = session.scalar(select(Group).where(Group.name == row['name']))
                    if existing:
                        logger.info(f"Group '{row['name']}' already exists, skipping")
                        skipped_count += 1
                        continue

                    group = Group(name=row['name'])
                    session.add(group)
                    loaded_count += 1
                    logger.info(f"Added group: {row['name']}")

                session.commit()
                logger.info(f"Groups loaded: {loaded_count}, skipped: {skipped_count}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error loading groups: {e}")
            raise
        finally:
            session.close()

    def load_subjects(self, csv_path: str):
        """Load subjects from CSV, checking for duplicates by name."""
        session = self.Session()
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                loaded_count = 0
                skipped_count = 0

                for row in reader:
                    # Check if subject exists
                    existing = session.scalar(select(Subject).where(Subject.name == row['name']))
                    if existing:
                        logger.info(f"Subject '{row['name']}' already exists, skipping")
                        skipped_count += 1
                        continue

                    subject = Subject(name=row['name'])
                    session.add(subject)
                    loaded_count += 1
                    logger.info(f"Added subject: {row['name']}")

                session.commit()
                logger.info(f"Subjects loaded: {loaded_count}, skipped: {skipped_count}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error loading subjects: {e}")
            raise
        finally:
            session.close()

    def load_auditoriums(self, csv_path: str):
        """Load auditoriums from CSV, checking for duplicates by (building, number)."""
        session = self.Session()
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                loaded_count = 0
                skipped_count = 0

                for row in reader:
                    # Check if auditorium exists by building and number
                    existing = session.scalar(
                        select(Auditorium).where(
                            Auditorium.building == row['building'],
                            Auditorium.number == row['number']
                        )
                    )
                    if existing:
                        logger.info(f"Auditorium '{row['building']}/{row['number']}' already exists, skipping")
                        skipped_count += 1
                        continue

                    auditorium = Auditorium(
                        name=row['name'],
                        number=row['number'],
                        building=row['building'],
                        floor=int(row['floor']),
                        capacity=int(row['capacity']) if row.get('capacity') else None,
                        type=row['type']
                    )
                    session.add(auditorium)
                    loaded_count += 1
                    logger.info(f"Added auditorium: {row['name']} ({row['building']})")

                session.commit()
                logger.info(f"Auditoriums loaded: {loaded_count}, skipped: {skipped_count}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error loading auditoriums: {e}")
            raise
        finally:
            session.close()

    def load_lesson_times(self, csv_path: str):
        """Load lesson times from CSV, checking for duplicates by lesson_number."""
        session = self.Session()
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                loaded_count = 0
                skipped_count = 0

                for row in reader:
                    # Check if lesson time exists
                    existing = session.scalar(
                        select(LessonTime).where(LessonTime.lesson_number == int(row['lesson_number']))
                    )
                    if existing:
                        logger.info(f"Lesson time #{row['lesson_number']} already exists, skipping")
                        skipped_count += 1
                        continue

                    # Parse time strings (format: HH:MM)
                    start_parts = row['start_time'].split(':')
                    end_parts = row['end_time'].split(':')

                    lesson_time = LessonTime(
                        lesson_number=int(row['lesson_number']),
                        start_time=time(int(start_parts[0]), int(start_parts[1])),
                        end_time=time(int(end_parts[0]), int(end_parts[1]))
                    )
                    session.add(lesson_time)
                    loaded_count += 1
                    logger.info(f"Added lesson time #{row['lesson_number']}: {row['start_time']}-{row['end_time']}")

                session.commit()
                logger.info(f"Lesson times loaded: {loaded_count}, skipped: {skipped_count}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error loading lesson times: {e}")
            raise
        finally:
            session.close()

    def load_all(self, data_dir: str = "./data"):
        """Load all CSV files in the correct order."""
        data_path = Path(data_dir)

        logger.info("Starting CSV data load...")

        # Load in correct order (respecting foreign key dependencies)
        if (data_path / "groups.csv").exists():
            logger.info("Loading groups...")
            self.load_groups(str(data_path / "groups.csv"))

        if (data_path / "subjects.csv").exists():
            logger.info("Loading subjects...")
            self.load_subjects(str(data_path / "subjects.csv"))

        if (data_path / "lesson_time.csv").exists():
            logger.info("Loading lesson times...")
            self.load_lesson_times(str(data_path / "lesson_time.csv"))

        if (data_path / "auditoriums.csv").exists():
            logger.info("Loading auditoriums...")
            self.load_auditoriums(str(data_path / "auditoriums.csv"))

        logger.info("CSV data load complete!")


if __name__ == "__main__":
    loader = CSVLoader(DATABASE_URL)
    loader.load_all()
