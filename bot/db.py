from datetime import datetime

import psycopg2
from logger import logger
from typing import Any, List

DB_NAME = "database"
DB_USER = "user"
DB_PASS = "password"
DB_HOST = "db"
DB_PORT = "5432"


def get_info_from_query(query: tuple | None) -> Any:
    if query:
        return query[0]
    return None

def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
    )


class DatabaseHandler:
    def __init__(self):
        self.conn = connect_db()
        self.create_tables()

    def __del__(self):
        self.conn.close()

    def create_tables(self):
        TABLES = [
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS lesson_time (
                lesson_number INTEGER PRIMARY KEY CHECK (lesson_number BETWEEN 1 AND 7),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS lessons (
                id SERIAL PRIMARY KEY,
                subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
                type VARCHAR(5) NOT NULL CHECK (type IN ('L', 'P'))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS groups (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS lesson_groups (
                lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
                group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
                lesson_date DATE NOT NULL,
                lesson_number INTEGER NOT NULL REFERENCES lesson_time(lesson_number) ON DELETE CASCADE,
                PRIMARY KEY (group_id, lesson_date, lesson_number)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                tg_id BIGINT UNIQUE,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL 
            );
            """,
        ]
        cur = self.conn.cursor()
        for table in TABLES:
            cur.execute(table)

        self.conn.commit()

    # Create
    def add_group(self, group_name: str) -> int | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id;
                """,
                (group_name,)
            )
            self.conn.commit()
            logger.info(f"Register group: {group_name}")
            return get_info_from_query(cur.fetchone())

    def attach_user_to_group(self, tg_id: int, username: str, group_name: str) -> int | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM groups 
                WHERE name = %s;
                """,
                (group_name,)
            )
            group_id = cur.fetchone()
            if not group_id:
                return None
            cur.execute(
                 """
                INSERT INTO users (tg_id, username, group_id) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (tg_id) 
                DO UPDATE SET 
                    group_id = EXCLUDED.group_id 
                RETURNING id;
                """,
                (tg_id, username, group_id)
            )
            self.conn.commit()
            logger.info(f"Add user: @{username}, with tg id: {tg_id}, to group: {group_id}")
            return get_info_from_query(cur.fetchone())


    def get_group_by_name(self, group_name: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM groups 
                WHERE name = %s;
                """,
                (group_name,)
            )
            return get_info_from_query(cur.fetchone())

    def get_subject_by_name(self, subject_name: str) -> int | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM subjects 
                WHERE name = %s;
                """,
                (subject_name,)
            )
            return get_info_from_query(cur.fetchone())

    def get_user_group(self, tg_id: int) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT group_id FROM users 
                WHERE tg_id = %s;
                """,
                (tg_id,)
            )
            return get_info_from_query(cur.fetchone())

    def set_default(self) -> None:
        self.set_default_lesson_time()
        self.set_default_subjects()

    def set_default_lesson_time(self) -> None:
        logger.info(f"Setting up default lesson time")
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lesson_time (lesson_number, start_time, end_time) VALUES
                (1, '09:00', '10:30'),
                (2, '10:40', '12:10'),
                (3, '12:20', '13:50'),
                (4, '14:20', '15:50'),
                (5, '16:00', '17:30'),
                (6, '18:00', '19:30'),
                (7, '19:50', '21:20')
                ON CONFLICT (lesson_number) DO UPDATE 
                SET start_time = EXCLUDED.start_time, 
                    end_time = EXCLUDED.end_time;
               """
            )
            self.conn.commit()

    def set_default_subjects(self) -> None:
        logger.info(f"Setting up subjects")
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subjects (name) VALUES
                ('Algorithms and DS'),
                ('ProbTheory&Stats'),
                ('DesignPatterns'),
                ('OS Software')
                ON CONFLICT (name) DO NOTHING;
                """
            )
            self.conn.commit()


    def add_lesson(self, subject_name: str, lesson_number: int, lesson_type: str):
        subject_id = self.get_subject_by_name(subject_name)

        if subject_id is None:
            logger.error(f"add_lesson: lesson {subject_name} does not exist")
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lessons (subject_id, lesson_number, type) 
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (subject_id, lesson_number, lesson_type)
            )
            self.conn.commit()
            logger.info(f"lesson added")
            return get_info_from_query(cur.fetchone())

    def add_lecture(self, group_names: List[str], lesson_date: datetime, subject_name: str, lesson_number: int) -> tuple | None:
        if group_names is None:
            return None
        group_ids = [self.get_group_by_name(group) for group in group_names if group is not None]
        group_ids = tuple(group_id for group_id in group_ids if group_id is not None)

        with self.conn.cursor() as cur:
            for i in range(len(group_ids)):
                cur.execute(
                    """
                    SELECT group_id, lesson_date
                    FROM lesson_groups 
                    WHERE group_id = %s AND lesson_date = %s
                    """,
                    (group_ids[i], lesson_date.strftime("%Y-%m-%d"))
                )
                self.conn.commit()
                res = get_info_from_query(cur.fetchone())
                if res:
                    logger.info(f"group {group_names[i]} already have pair")
                    return None

        lesson_id = self.add_lesson(subject_name, lesson_number, "L")
        if lesson_id is None:
            return None

        with self.conn.cursor() as cur:
            for i in range(len(group_ids)):
                cur.execute(
                    """
                    INSERT INTO lesson_groups (lesson_id, group_id, lesson_date) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (group_id, lesson_date) DO NOTHING
                    RETURNING lesson_id;
                    """,
                    (lesson_id, group_ids[i], lesson_date.strftime("%Y-%m-%d"))
                )
            self.conn.commit()
            logger.info(f"Lecture added to groups {group_names}")
            return get_info_from_query(cur.fetchall())

    def add_practice_to_group(self, group_name: str, lesson_date: datetime, subject_name: str, lesson_number: int) -> None:
        group_id = self.get_group_by_name(group_name)
        if group_id is None:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT group_id, lesson_date
                FROM lesson_groups 
                WHERE group_id = %s AND lesson_date = %s
                """,
                (group_id, lesson_date.strftime("%Y-%m-%d"))
            )
            self.conn.commit()
            res = get_info_from_query(cur.fetchone())
            if res:
                logger.info(f"group {group_name} already have pair")
                return None

        lesson_id = self.add_lesson(subject_name, lesson_number, "P")
        if lesson_id is None:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lesson_groups (lesson_id, group_id, lesson_date) 
                VALUES (%s, %s, %s)
                ON CONFLICT (group_id, lesson_date) DO NOTHING
                RETURNING lesson_id;
                """,
                (lesson_id, group_id, lesson_date.strftime("%Y-%m-%d"))
            )
            self.conn.commit()
            logger.info(f"lesson added to group")
            return get_info_from_query(cur.fetchone())

    def get_lessons_for_group_on_date(self, group_name: str, lesson_date: datetime):
        group_id = self.get_group_by_name(group_name)
        if group_id is None:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    s.name AS subject_name,
                    l.type,
                    lt.start_time,
                    lt.end_time
                FROM lesson_groups lg
                JOIN lessons l ON lg.lesson_id = l.id
                JOIN subjects s ON l.subject_id = s.id
                JOIN lesson_time lt ON l.lesson_number = lt.lesson_number
                WHERE lg.group_id = %s AND lg.lesson_date = %s
                ORDER BY l.lesson_number;
                """,
                (group_id, lesson_date.strftime("%Y-%m-%d"))
            )
            lessons = [LessonMessage(*item) for item in cur.fetchall()]
            logger.info(
                f"Returning {len(lessons)} lessons for group '{group_name}' on {lesson_date.strftime('%Y-%m-%d')}")
            return lessons

    def get_lessons_for_user_on_date(self, tg_id: int, lesson_date: datetime):
        group_id = self.get_user_group(tg_id)
        if group_id is None:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    s.name AS subject_name,
                    l.type,
                    lt.start_time,
                    lt.end_time
                FROM lesson_groups lg
                JOIN lessons l ON lg.lesson_id = l.id
                JOIN subjects s ON l.subject_id = s.id
                JOIN lesson_time lt ON l.lesson_number = lt.lesson_number
                WHERE lg.group_id = %s AND lg.lesson_date = %s
                ORDER BY l.lesson_number;
                """,
                (group_id, lesson_date.strftime("%Y-%m-%d"))
            )
            lessons = [LessonMessage(*item) for item in cur.fetchall()]
            logger.info(
                f"Returning {len(lessons)} lessons for user: '{tg_id}' on {lesson_date.strftime('%Y-%m-%d')}")
            return lessons

class LessonMessage:
    def __init__(self, subject_name: str, lesson_type: str, lesson_start: datetime, lesson_end: datetime) -> None:
        self.subject_name = subject_name
        self.lesson_type = lesson_type
        self.lesson_start = lesson_start
        self.lesson_end = lesson_end

    def __repr__(self) -> str:
        return f"{self.subject_name} ({self.lesson_type}): {self.lesson_start.strftime("%H:%M")} - {self.lesson_end.strftime("%H:%M")}\n"