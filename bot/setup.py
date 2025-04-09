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

    database.create_lesson_and_add_groups(["23-LR-CS", "23-LR-JA", "23-LR-JS"], datetime.today(), 6, "ProbTheory&Stats", "Lecture")
    database.create_lesson_and_add_groups(["23-LR-JS"], datetime.today(), 7, "Algorithms and DS", "Practice")
    database.create_lesson_and_add_groups(["23-LR-JA"], datetime.today(), 7, "Algorithms and DS", "Practice")

    database.create_lesson_and_add_groups(["23-LR-CS", "23-LR-JA", "23-LR-JS"], datetime.today() + timedelta(days=1), 6, "Algorithms and DS", "Lecture")

    database.create_lesson_and_add_groups(["23-HO"], datetime.today(), 1, "SQL&DataProc", "Practice")
    database.create_lesson_and_add_groups(["23-HR-CS1"], datetime.today(), 2, "ProbTheory&Stats", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JA1", "23-HR-JA2", "23-HR-CS1", "23-HR-CS2", "23-HR-JS1", "23-HR-JS2","23-HO"], datetime.today(), 3, "ProbTheory&Stats", "Lecture")
    database.create_lesson_and_add_groups(["23-HR-JS1"], datetime.today(), 5, "Automated testing", "Practice")
    database.create_lesson_and_add_groups(["23-HO"], datetime.today(), 6, "Automated testing", "Practice")

    database.create_lesson_and_add_groups(["23-HR-JA1", "23-HR-JA2", "23-HR-CS1", "23-HR-CS2", "23-HR-JS1", "23-HR-JS2","23-HO"], datetime.today() + timedelta(days=1), 2, "ProbTheory&Stats", "Lecture")
    database.create_lesson_and_add_groups(["23-HR-CS1"], datetime.today() + timedelta(days=1), 3, "Multythread. C#", "Practice")
    database.create_lesson_and_add_groups(["23-HR-CS2"], datetime.today() + timedelta(days=1), 3, "SQL&DataProc", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JS1"], datetime.today() + timedelta(days=1), 3, "Modern JS WebDev", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JS2"], datetime.today() + timedelta(days=1), 3, "ProbTheory&Stats", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JS2"], datetime.today() + timedelta(days=1), 4, "Modern JS WebDev", "Practice")


    database.create_lesson_and_add_groups(["23-HR-CS1", "23-HR-CS2"], datetime.today() + timedelta(days=2), 1, "Multythread. C#", "Lecture")
    database.create_lesson_and_add_groups(["23-HR-JA1"], datetime.today() + timedelta(days=2), 1, "Automated testing", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JS1", "23-LR-JS2", "23-HO"], datetime.today() + timedelta(days=2), 1, "Modern JS WebDev", "Lecture")
    database.create_lesson_and_add_groups(["23-HR-CS2"], datetime.today() + timedelta(days=2), 2, "Automated testing", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JS2"], datetime.today() + timedelta(days=2), 2, "ProbTheory&Stats", "Practice")
    database.create_lesson_and_add_groups(["23-HR-JA1", "23-HR-JA2", "23-HR-CS1", "23-HR-CS2", "23-HR-JS1", "23-HR-JS2","23-HO"], datetime.today() + timedelta(days=2), 3, "IP Law Basics", "Lecture")



