from datetime import datetime, timedelta

from db import DBManager
from config import DATABASE_URL

if __name__ == '__main__':
    database = DBManager(DATABASE_URL)

    database.set_default()

    database.create_group("23-LR-CS")
    database.create_group("23-LR-JA")
    database.create_group("23-LR-JS")

    database.create_group("23-HR-JA1")
    database.create_group("23-HR-JA2")
    database.create_group("23-HR-CS1")
    database.create_group("23-HR-CS2")
    database.create_group("23-HR-JS1")
    database.create_group("23-HR-JS2")
    database.create_group("23-HO")

    database.create_lesson_and_add_groups(["23-LR-CS", "23-LR-JA", "23-LR-JS"], datetime.today(), 6, "Algorithms and DS", "Lecture")

    database.create_lesson_and_add_groups(["23-HR-JA1", "23-HR-JA2", "23-HR-CS1", "23-HR-CS2", "23-HR-JS1", "23-HR-JS2","23-HO"], datetime.today() + timedelta(days=0), 2, "ProbTheory&Stats", "Lecture", "aud 327")
    database.create_lesson_and_add_groups(["23-HR-CS1"], datetime.today() + timedelta(days=0), 3, "Multythread. C#", "Practice", "aud 330")
    database.create_lesson_and_add_groups(["23-HR-CS2"], datetime.today() + timedelta(days=0), 3, "SQL&DataProc", "Practice", "aud 339")
    database.create_lesson_and_add_groups(["23-HR-JS1"], datetime.today() + timedelta(days=0), 3, "Modern JS WebDev", "Practice", "aud 341")
    database.create_lesson_and_add_groups(["23-HR-JS2"], datetime.today() + timedelta(days=0), 3, "ProbTheory&Stats", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JS2"], datetime.today() + timedelta(days=0), 4, "Modern JS WebDev", "Practice")


    database.create_lesson_and_add_groups(["23-HR-CS1", "23-HR-CS2"], datetime.today() + timedelta(days=1), 1, "Multythread. C#", "Lecture")
    database.create_lesson_and_add_groups(["23-HR-JA1"], datetime.today() + timedelta(days=1), 1, "Automated testing", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JS1", "23-LR-JS2", "23-HO"], datetime.today() + timedelta(days=1), 1, "Modern JS WebDev", "Lecture")
    database.create_lesson_and_add_groups(["23-HR-CS2"], datetime.today() + timedelta(days=1), 2, "Automated testing", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JS2"], datetime.today() + timedelta(days=1), 2, "ProbTheory&Stats", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JA1", "23-HR-JA2", "23-HR-CS1", "23-HR-CS2", "23-HR-JS1", "23-HR-JS2","23-HO"], datetime.today() + timedelta(days=1), 3, "IP Law Basics", "Lecture")