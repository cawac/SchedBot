"""add initial data for lesson time and subjects

Revision ID: f285ecb31441
Revises: d7c2df9ef34b
Create Date: 2025-10-05 15:47:42.407461

"""
from datetime import time
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f285ecb31441'
down_revision: Union[str, Sequence[str], None] = 'd7c2df9ef34b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


lesson_times = (
    (1, time(9, 0), time(10, 30)),
    (2, time(10, 40), time(12, 10)),
    (3, time(12, 20), time(13, 50)),
    (4, time(14, 20), time(15, 50)),
    (5, time(16, 0), time(17, 30)),
    (6, time(18, 0), time(19, 30)),
    (7, time(19, 50), time(21, 20)),
)

subjects = (
    "DesignPatterns",
    "Algorithms and DS",
    "ProbTheory&Stats",
    "OS Software",
    "SQL&DataProc",
    "Multythread. JA",
    "Modern JS WebDev",
    "Automated testing",
    "Multythread. C#",
    "IP Law Basics",
    "WebDev JS",
    "Intro to DT",
    "Disc Math",
    "OOP Java",
    "English",
    "Func Sftw Testing",
    "High Math",
    "CloudTech",
    "Cryptogr&Blockchain",
    "Моbile Dev Kotlin",
    "UX/UI design",
    "Team project",
    "Моbile Dev React Native",
    "Project Planning Method",
    "Machine Learning",
    "BA basics",
    "WebDev with .NET",
    "PM basics"
)

lesson_time_table = sa.Table(
    "lesson_time",
    sa.MetaData(),
    sa.Column("lesson_number", sa.Integer, primary_key=True),
    sa.Column("start_time", sa.Time, nullable=False),
    sa.Column("end_time", sa.Time, nullable=False),
)

subject_table = sa.Table(
    "subjects",
    sa.MetaData(),
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String, nullable=False),
)

def upgrade():
    conn = op.get_bind()

    conn.execute(
        lesson_time_table.insert(),
        [
            {"lesson_number": num, "start_time": start, "end_time": end}
            for num, start, end in lesson_times
        ]
    )

    conn.execute(
        subject_table.insert(),
        [{"name": s} for s in subjects]
    )

def downgrade():
    conn = op.get_bind()
    conn.execute(
        lesson_time_table.delete().where(
            lesson_time_table.c.lesson_number.in_(list(range(1, 8)))
        )
    )
    conn.execute(
        subject_table.delete().where(
            subject_table.c.name.in_(subjects)
        )
    )
