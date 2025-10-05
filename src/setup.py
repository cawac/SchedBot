from datetime import timedelta

from config import now_local
from db import database_manager
from parser import Parser, get_all_file_paths

if __name__ == '__main__':
    database = database_manager
    database.set_default()

    amount_of_days = 100
    parser = Parser()

    # urls = f"https://docs.google.com/spreadsheets/d/1lgRVGshD1Cyjg_Cex73K--wySnQMi5TUsojz0JlTfB0/edit?gid=0#gid=0"
    #
    # response = requests.get(urls)
    #
    # with open("schedules/spreadsheet.xlsx", "wb") as f:
    #     f.write(response.content)

    for file_path in get_all_file_paths("schedules"):
        parser.load_schedule(file_path, min_column=6, min_row=4, max_column=13, max_row=863)
        for group in parser.get_all_groups():
            database.create_group(group)
        for i in range(amount_of_days):
            current_date = now_local() + timedelta(days=i)
            lessons_on_day = parser.parse_lessons_for_day(now_local() + timedelta(days=i))

            if lessons_on_day is None:
                continue

            for lesson in lessons_on_day:
                database.create_lesson_and_add_groups(
                    lesson["groups"],
                    current_date,
                    lesson["lesson_number"],
                    lesson["subject_name"],
                    lesson["lesson_type"],
                    lesson["auditorium"]
                )
