import datetime

from parser import *


if __name__ == '__main__':
    parser = Parser()

    day = datetime(2025, 4, 28)

    for file_path in get_all_file_paths("schedules"):
        parser.load_schedule(file_path, min_column=6, min_row=4, max_column=13, max_row=863)
        print("groups:", parser.get_all_groups())

        current_date = day
        lessons_on_day = parser.parse_lessons_for_day(current_date)

        if lessons_on_day is None:
            continue

        print("lessons_on_day:", lessons_on_day)
