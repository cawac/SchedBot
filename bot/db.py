from datetime import datetime

import psycopg2
from logger import logger
from typing import Any

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
                lesson_number INTEGER NOT NULL REFERENCES lesson_time(lesson_number) ON DELETE CASCADE,
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
                PRIMARY KEY (lesson_id, group_id)
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

    def add_user_to_group(self, tg_id: int, username: str, group_name: str) -> int | None:
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
                return
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
        self.add_group("23-LR-CS")

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

    def add_lesson_to_group(self, group_name: str, lesson_date: datetime, subject_name: str, lesson_number: int, lesson_type: str) -> None:
        lesson_id = self.add_lesson(subject_name, lesson_number, lesson_type)
        if lesson_id is None:
            return None

        group_id = self.get_group_by_name(group_name)
        if group_id is None:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lesson_groups (lesson_id, group_id, lesson_date) 
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
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
                SELECT lesson_id
                FROM lesson_groups
                WHERE group_id = %s AND lesson_date = %s
                """,
                (group_id, lesson_date.strftime("%Y-%m-%d")))
            logger.info(f"returning lesson for group {group_name}")
            return cur.fetchall()