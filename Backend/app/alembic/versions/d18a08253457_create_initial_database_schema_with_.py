"""Create initial database schema with teachers, courses, lessons and course_teachers tables

Revision ID: d18a08253457
Revises: 
Create Date: 2025-06-13 15:02:43.050784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd18a08253457'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create teachers table
    op.create_table(
        'teachers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_teachers_email'), 'teachers', ['email'], unique=False)
    op.create_index(op.f('ix_teachers_id'), 'teachers', ['id'], unique=False)

    # Create courses table
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('thumbnail', sa.String(length=500), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_courses_id'), 'courses', ['id'], unique=False)
    op.create_index(op.f('ix_courses_slug'), 'courses', ['slug'], unique=False)

    # Create lessons table
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lessons_course_id'), 'lessons', ['course_id'], unique=False)
    op.create_index(op.f('ix_lessons_id'), 'lessons', ['id'], unique=False)
    op.create_index(op.f('ix_lessons_slug'), 'lessons', ['slug'], unique=False)

    # Create course_teachers association table
    op.create_table(
        'course_teachers',
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id']),
        sa.PrimaryKeyConstraint('course_id', 'teacher_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order to avoid foreign key constraint issues
    op.drop_table('course_teachers')
    op.drop_index(op.f('ix_lessons_slug'), table_name='lessons')
    op.drop_index(op.f('ix_lessons_id'), table_name='lessons')
    op.drop_index(op.f('ix_lessons_course_id'), table_name='lessons')
    op.drop_table('lessons')
    op.drop_index(op.f('ix_courses_slug'), table_name='courses')
    op.drop_index(op.f('ix_courses_id'), table_name='courses')
    op.drop_table('courses')
    op.drop_index(op.f('ix_teachers_id'), table_name='teachers')
    op.drop_index(op.f('ix_teachers_email'), table_name='teachers')
    op.drop_table('teachers')
