import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date
from parser.schedule_parser import ScheduleParser, get_lesson_info, is_yellow


class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = ScheduleParser()
        self.parser.load_worksheet("TestTable.xlsx", min_row=4, max_row=1000, min_column=6, max_column=14)
        self.parser.get_all_groups()

        mock_sheet = MagicMock()
        self.parser._Parser__sheet = mock_sheet

    def test_is_yellow_true(self):
        mock_cell = MagicMock()
        mock_cell.fill.fgColor.type = "rgb"
        mock_cell.fill.fgColor.rgb = "FFFFFF00"
        self.assertTrue(is_yellow(mock_cell))

    def test_is_yellow_false(self):
        mock_cell = MagicMock()
        mock_cell.fill.fgColor.type = "rgb"
        mock_cell.fill.fgColor.rgb = "FF000000"
        self.assertFalse(is_yellow(mock_cell))

    def test_get_all_groups(self):
        self.parser._Parser__sheet.cell.side_effect = lambda row, column: MagicMock(value=f"Group {row}") if column == 5 else None
        expected_groups = ['Group 4', 'Group 5']
        actual_groups = self.parser.get_all_groups()
        self.assertEqual(expected_groups, actual_groups)

    def test_parse_lessons_for_day_empty(self):
        self.parser.get_row_coordinates_by_day = MagicMock(return_value=None)
        result = self.parser.parse_lessons_for_day(datetime(2025, 3, 3))
        self.assertEqual(result, [])

    @patch("parser.get_lesson_info")
    def test_parse_lessons_for_day_valid(self, mock_get_lesson_info):
        self.parser.get_row_coordinates_by_day = MagicMock(return_value=4)

        mock_cell = MagicMock()
        mock_cell.value = "Some lesson"
        self.parser._Parser__sheet.cell.return_value = mock_cell

        mock_get_lesson_info.return_value = {
            "date": datetime(2025, 3, 3),
            "groups": ["Group 1"],
            "lesson_number": 1,
            "subject_name": "Math",
            "lesson_type": "Lecture",
            "auditorium": "101"
        }

        lessons = self.parser.parse_lessons_for_day(datetime(2025, 3, 3))
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["subject_name"], "Math")

    def test_get_row_coordinates_by_day_found(self):
        mock_cell = MagicMock()
        mock_cell.value = datetime(2025, 3, 3)
        self.parser._Parser__sheet.iter_rows.return_value = [[mock_cell]]
        result = self.parser.get_row_coordinates_by_day(datetime(2025, 3, 3))
        self.assertEqual(result, mock_cell.row)

    def test_get_row_coordinates_by_day_not_found(self):
        mock_cell = MagicMock()
        mock_cell.value = "Text"
        self.parser._Parser__sheet.iter_rows.return_value = [[mock_cell]]
        result = self.parser.get_row_coordinates_by_day(datetime(2025, 3, 3))
        self.assertIsNone(result)


class TestLessonInfoExtraction(unittest.TestCase):
    def test_get_lesson_info_parse(self):
        mock_sheet = MagicMock()
        mock_sheet.cell.side_effect = lambda row, col: MagicMock(value={
            (2, 6): 1,
            (4, 5): "Group A",
            (3, 3): datetime(2025, 3, 3),
            (4, 6): "Math (L) aud 101"
        }.get((row, col), None))

        info = get_lesson_info(mock_sheet, 4, 6)
        self.assertEqual(info["subject_name"], "Math")
        self.assertEqual(info["lesson_type"], "Lecture")
        self.assertEqual(info["auditorium"], "101")
        self.assertEqual(info["groups"], ["Group A"])
        self.assertEqual(info["lesson_number"], 1)
        self.assertEqual(info["date"].date(), date(2025, 3, 3))


if __name__ == '__main__':
    unittest.main()
