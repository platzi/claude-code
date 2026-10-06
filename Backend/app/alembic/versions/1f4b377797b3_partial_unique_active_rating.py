"""partial unique active rating

Reemplaza UNIQUE(course_id, user_id, deleted_at) por un índice único parcial
sobre (course_id, user_id) WHERE deleted_at IS NULL.

El constraint original no evitaba duplicados activos: en PostgreSQL NULL != NULL,
así que dos filas con deleted_at IS NULL nunca colisionaban.

Revision ID: 1f4b377797b3
Revises: 0e3a8766f785
Create Date: 2026-09-29 02:08:33.148654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f4b377797b3'
down_revision: Union[str, None] = '0e3a8766f785'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Un solo rating activo por usuario y curso."""

    # 1. Deduplicar ratings activos: conservar el más reciente por (course_id, user_id)
    #    y hacer soft delete del resto, para que el índice único pueda crearse.
    op.execute(
        """
        UPDATE course_ratings SET deleted_at = NOW(), updated_at = NOW()
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY course_id, user_id
                    ORDER BY updated_at DESC, id DESC
                ) AS rn
                FROM course_ratings
                WHERE deleted_at IS NULL
            ) t
            WHERE rn > 1
        )
        """
    )

    # 2. Eliminar el UNIQUE compuesto que no protegía los ratings activos
    op.drop_constraint(
        'uq_course_ratings_user_course_deleted',
        'course_ratings',
        type_='unique'
    )

    # 3. Índice único parcial: solo aplica a filas activas (deleted_at IS NULL),
    #    los soft-deletes quedan fuera y se puede volver a calificar.
    op.create_index(
        'uq_course_ratings_active_user_course',
        'course_ratings',
        ['course_id', 'user_id'],
        unique=True,
        postgresql_where=sa.text('deleted_at IS NULL')
    )


def downgrade() -> None:
    """Downgrade schema - Restaurar el UNIQUE compuesto original.

    Nota: la deduplicación del upgrade NO se revierte; los ratings duplicados
    quedan con soft delete.
    """

    op.drop_index(
        'uq_course_ratings_active_user_course',
        table_name='course_ratings',
        postgresql_where=sa.text('deleted_at IS NULL')
    )

    op.create_unique_constraint(
        'uq_course_ratings_user_course_deleted',
        'course_ratings',
        ['course_id', 'user_id', 'deleted_at']
    )
