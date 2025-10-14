"""add course_ratings table

Revision ID: 0e3a8766f785
Revises: d18a08253457
Create Date: 2025-10-14 18:31:32.754640

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e3a8766f785'
down_revision: Union[str, None] = 'd18a08253457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create course_ratings table."""

    # Crear tabla course_ratings
    op.create_table(
        'course_ratings',

        # Columnas heredadas de BaseModel
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),

        # Columnas específicas del rating
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['course_id'],
            ['courses.id'],
            name='fk_course_ratings_course_id'
        ),
        sa.CheckConstraint(
            'rating >= 1 AND rating <= 5',
            name='ck_course_ratings_rating_range'
        ),

        # UNIQUE constraint compuesto con deleted_at
        # Permite múltiples soft-deletes del mismo user_id + course_id
        sa.UniqueConstraint(
            'course_id',
            'user_id',
            'deleted_at',
            name='uq_course_ratings_user_course_deleted'
        )
    )

    # Crear índices para optimización de queries
    op.create_index(
        op.f('ix_course_ratings_id'),
        'course_ratings',
        ['id'],
        unique=False
    )
    op.create_index(
        op.f('ix_course_ratings_course_id'),
        'course_ratings',
        ['course_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_course_ratings_user_id'),
        'course_ratings',
        ['user_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - Drop course_ratings table."""

    # Eliminar índices primero
    op.drop_index(op.f('ix_course_ratings_user_id'), table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_course_id'), table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_id'), table_name='course_ratings')

    # Eliminar tabla
    op.drop_table('course_ratings')
