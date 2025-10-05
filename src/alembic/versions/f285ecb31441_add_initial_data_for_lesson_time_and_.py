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
down_revision: Union[str, Sequence[str], None] = '97f79d5bffcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


lesson_times = (
    (1, time(9, 0), time(10, 30)),
    (2, time(10, 40), time(12, 10)),
    (3, time(12, 20), time(13, 50)),
    (4, time(14, 20), time(15, 50)),
    (5, time(16, 0), time(17, 30)),
    (6, time(18, 0), time(19, 30)),
    (7, time(19, 40), time(21, 10)),
)

lesson_time_table = sa.Table(
    "lesson_time",
    sa.MetaData(),
    sa.Column("lesson_number", sa.Integer, primary_key=True),
    sa.Column("start_time", sa.Time, nullable=False),
    sa.Column("end_time", sa.Time, nullable=False),
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

def downgrade():
    conn = op.get_bind()
    conn.execute(
        lesson_time_table.delete().where(
            lesson_time_table.c.lesson_number.in_(list(range(1, 8)))
        )
    )
