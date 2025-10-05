from db import database_manager
from parser.simple_parser import ScheduleParser, get_all_file_paths, merge_dicts

if __name__ == '__main__':
    parser = ScheduleParser()

    result = {}
    for file_path in get_all_file_paths('schedules'):
        merge_dicts(result, parser.load_file(file_path))

    for group in result['groups']:
        database_manager.create_group(name=group)

    for lesson in result['lessons']:
        if all(lesson.values()):
            database_manager.create_lesson_and_add_groups(lesson['groups'], lesson['lesson_date'],
                                                          lesson['lesson_number'], lesson['lesson_info'],
                                                          None, None)
        else:
            print(lesson)