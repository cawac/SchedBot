"""add auditoriums and user_actions

Revision ID: a1b2c3d4e5f6
Revises: f285ecb31441
Create Date: 2026-06-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f285ecb31441'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create auditoriums table
    op.create_table('auditoriums',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('number', sa.String(length=20), nullable=True),
        sa.Column('building', sa.String(length=100), nullable=False),
        sa.Column('floor', sa.Integer(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=30), nullable=False, server_default='CLASSROOM'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_auditorium_building_number', 'auditoriums', ['building', 'number'])

    # Create user_actions table
    op.create_table('user_actions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('command_name', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_action_user_id', 'user_actions', ['user_id'])
    op.create_index('ix_user_action_timestamp', 'user_actions', ['timestamp'])
    op.create_index('ix_user_action_command', 'user_actions', ['command_name'])

    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Extract unique auditoriums from lessons.auditorium and populate auditoriums table
    # Create temporary mapping
    conn = op.get_bind()

    # Get unique auditoriums from lessons (excluding NULL)
    result = conn.execute(sa.text("""
        SELECT DISTINCT auditorium
        FROM lessons
        WHERE auditorium IS NOT NULL
    """))

    unique_auditoriums = [row[0] for row in result]

    # Parse auditorium strings and insert into auditoriums table
    for aud_str in unique_auditoriums:
        # Extract number from auditorium string
        # Assuming format like "101", "201A", "Lab 302", etc.
        number = ''.join(filter(str.isdigit, aud_str))
        if number:
            floor = int(number[0]) if len(number) > 0 else 1
        else:
            floor = 1
            number = None

        # Determine type based on auditorium name
        aud_type = 'CLASSROOM'
        aud_lower = aud_str.lower()
        if 'lab' in aud_lower or 'laboratory' in aud_lower:
            aud_type = 'LAB'
        elif 'lecture' in aud_lower or 'hall' in aud_lower:
            aud_type = 'LECTURE_HALL'
        elif 'computer' in aud_lower or 'comp' in aud_lower:
            aud_type = 'COMPUTER_LAB'
        elif 'seminar' in aud_lower:
            aud_type = 'SEMINAR_ROOM'

        # Insert auditorium
        conn.execute(sa.text("""
            INSERT INTO auditoriums (name, number, building, floor, capacity, type)
            VALUES (:name, :number, :building, :floor, :capacity, :type)
        """), {
            'name': aud_str,
            'number': number,
            'building': 'Main Building',  # Default building
            'floor': floor,
            'capacity': 30,  # Default capacity
            'type': aud_type
        })

    # Add auditorium_id column to lessons
    op.add_column('lessons', sa.Column('auditorium_id', sa.Integer(), nullable=True))

    # Populate auditorium_id based on auditorium string match
    conn.execute(sa.text("""
        UPDATE lessons l
        SET auditorium_id = a.id
        FROM auditoriums a
        WHERE l.auditorium = a.name
    """))

    # Drop old auditorium column
    op.drop_column('lessons', 'auditorium')

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_lessons_auditorium_id',
        'lessons', 'auditoriums',
        ['auditorium_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Add back auditorium string column
    op.add_column('lessons', sa.Column('auditorium', sa.String(length=20), nullable=True))

    # Populate auditorium from auditorium_id
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE lessons l
        SET auditorium = a.name
        FROM auditoriums a
        WHERE l.auditorium_id = a.id
    """))

    # Drop foreign key and auditorium_id column
    op.drop_constraint('fk_lessons_auditorium_id', 'lessons', type_='foreignkey')
    op.drop_column('lessons', 'auditorium_id')

    # Drop user_actions table
    op.drop_index('ix_user_action_command', table_name='user_actions')
    op.drop_index('ix_user_action_timestamp', table_name='user_actions')
    op.drop_index('ix_user_action_user_id', table_name='user_actions')
    op.drop_table('user_actions')

    # Drop auditoriums table
    op.drop_index('ix_auditorium_building_number', table_name='auditoriums')
    op.drop_table('auditoriums')

    # Drop is_admin column from users
    op.drop_column('users', 'is_admin')
